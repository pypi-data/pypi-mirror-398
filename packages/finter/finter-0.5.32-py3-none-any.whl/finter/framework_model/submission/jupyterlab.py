import os
import re
import threading
import time
import asyncio
from typing import Any, Tuple

from IPython.display import HTML, display
from ipywidgets import IntText, widgets
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

from finter.framework_model.submission.config import get_model_info
from finter.framework_model.submission.helper_notebook import NotebookExtractor
from finter.framework_model.submission.helper_path import FileManager
from finter.framework_model.submission.helper_position import load_model_instance
from finter.framework_model.submission.helper_submission import submit_model
from finter.framework_model.submission.helper_ui import MAC_STYLE
from finter.framework_model.validation import ValidationHelper
from finter.api.alpha_api import AlphaApi
from finter.api_client import ApiClient
from dotenv import load_dotenv
import requests


def name_exist(model_type, model_universe, model_name):
    load_dotenv()
    check_url = "https://api.finter.quantit.io/user_info?item=username"
    check_header = {
        "accept": "application/json",
        "Authorization": f"Token {os.environ.get('FINTER_API_KEY')}",
    }
    try:
        user_name = requests.get(check_url, headers=check_header).json()["data"]
    except:
        return False

    try:
        am_list = (
            AlphaApi(ApiClient()).alpha_identities_retrieve().am_identity_name_list
        )
    except:
        return False

    check_list = [user_name, model_type.lower()]

    if model_universe == "kr_stock":
        check_list.extend(["krx", "stock"])
    elif model_universe == "us_etf":
        check_list.extend(["us", "compustat", "etf"])
    elif model_universe == "us_stock":
        check_list.extend(["us", "compustat", "stock"])
    elif model_universe == "us_future":
        check_list.extend(["us", "bloomberg", "future"])
    elif model_universe == "vn_stock":
        check_list.extend(["vnm", "fiintek", "stock"])
    elif model_universe == "id_stock":
        check_list.extend(["id", "compustat", "stock"])
    elif model_universe == "btcusdt_spot_binance":
        check_list.extend(["crypto", "binance", "spot"])

    # 모든 check_list 요소들이 am에 포함되어 있는지 확인
    own_am_list = [
        am.split(".")[-1]
        for am in am_list
        if all(element in am.split(".") for element in check_list)
    ]

    if model_name in own_am_list:
        return True
    return False

AVAILABLE_MARKETS = [
    "kr_stock",
    "us_etf",
    "us_stock",
    "us_future",
    "vn_stock",
    "id_stock",
    "id_bond",
    "id_fund",
    "btcusdt_spot_binance",
    "world",
]


class JupyterLabSubmission(NotebookExtractor):
    def __init__(
        self,
        start_date: int = 20150101,
        end_date: int = 20231231,
        model_name: str = "",
        model_universe: str = "kr_stock",
        gpu: bool = False,
        bypass_validate: bool = False,
        ignore_local_validation: bool = False,
        submission_start_date: str = "",
        benchmark: str = "",
        insample: str = "",
        use_sidecar: bool = True,
    ):
        super().__init__()

        self.start_date = start_date
        self.end_date = end_date
        self.default_modelname = model_name
        self.default_model_universe = model_universe
        self.default_gpu = gpu
        self.default_bypass_validate = bypass_validate
        self.default_ignore_local_validation = ignore_local_validation
        self.default_submission_start_date = submission_start_date
        self.default_benchmark = benchmark
        self.default_insample = insample
        self.use_sidecar = use_sidecar

        # Cache the main thread event loop for thread-safe UI updates
        try:
            self._loop = asyncio.get_event_loop()
        except Exception:
            self._loop = None

        self.setup_ui()
        self.register_event_handlers()
        self.update_info_display()

    def setup_ui(self):
        if self.use_sidecar:
            # Reuse existing sidecar if available, otherwise create new one
            if not hasattr(self, 'sidecar') or self.sidecar is None:
                self.setup_sidecar()
        else:
            self.sidecar = None
            # Create a persistent output widget for cell mode
            if not hasattr(self, 'cell_output'):
                self.cell_output = widgets.Output()
                display(self.cell_output)
        self.create_widgets()
        self.setup_layout()

    def setup_sidecar(self):
        try:
            from sidecar import Sidecar
            self.sidecar = Sidecar(title="Submission Dashboard")
        except ImportError:
            print("Warning: sidecar not available, displaying in output cell")
            self.sidecar = None
            self.use_sidecar = False

    def create_widgets(self):
        self.model_name_input, self.model_universe_dropdown = (
            self.create_input_widgets()
        )

        self.title = self.create_title_widget()
        self.code_display = self.create_code_display_widget()

        self.status_output = widgets.Output()
        (
            self.submit_button,
            self.cancel_button,
            self.position_button,
            self.simulation_button,
            self.refresh_button,
            self.progress,
        ) = self.create_action_widgets()

        self.start_date_input = IntText(
            value=self.start_date,
            description="Start",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="auto"),
        )
        self.end_date_input = IntText(
            value=self.end_date,
            description="End",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="auto"),
        )

        # Add submission option checkboxes
        self.gpu_checkbox = widgets.Checkbox(
            value=self.default_gpu,
            description="GPU",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="auto"),
        )
        self.bypass_validate_checkbox = widgets.Checkbox(
            value=self.default_bypass_validate,
            description="Bypass Validate",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="auto"),
        )
        self.ignore_local_validation_checkbox = widgets.Checkbox(
            value=self.default_ignore_local_validation,
            description="Ignore Local Validation",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="auto"),
        )

        # Add submission start date input (optional)
        self.submission_start_date_input = widgets.Text(
            value=self.default_submission_start_date,
            description="Start Date (Submit)",
            placeholder="YYYYMMDD (optional)",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="300px"),
        )

        # Add benchmark input (optional)
        self.benchmark_input = widgets.Text(
            value=self.default_benchmark,
            description="Benchmark",
            placeholder="benchmark name (optional)",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="300px"),
        )

        # Add insample input (optional, mutually exclusive with submission_start_date)
        self.insample_input = widgets.Text(
            value=self.default_insample,
            description="Insample",
            placeholder="e.g., 20day (optional)",
            style={"description_width": "initial"},
            layout=widgets.Layout(width="300px"),
        )

        # Create section headers
        self.submit_options_header = widgets.HTML(
            value="<h3 style='margin: 20px 0 10px 0; color: #2c3e50;'>Submission Options</h3>"
        )
        self.analysis_options_header = widgets.HTML(
            value="<h3 style='margin: 20px 0 10px 0; color: #2c3e50;'>Analysis Options (Position/Simulation)</h3>"
        )

    def setup_layout(self):
        layout = widgets.VBox(
            [
                self.title,
                # Submission Options Section
                self.submit_options_header,
                widgets.HBox(
                    [self.model_name_input, self.model_universe_dropdown],
                    layout=widgets.Layout(margin="0 0 10px 0"),
                ),
                widgets.HBox(
                    [self.gpu_checkbox, self.bypass_validate_checkbox, self.ignore_local_validation_checkbox],
                    layout=widgets.Layout(margin="0 0 10px 0"),
                ),
                widgets.HBox(
                    [self.submission_start_date_input, self.insample_input],
                    layout=widgets.Layout(margin="0 0 10px 0"),
                ),
                widgets.HBox(
                    [self.benchmark_input],
                    layout=widgets.Layout(margin="0 0 10px 0"),
                ),
                # Analysis Options Section
                self.analysis_options_header,
                widgets.HBox(
                    [self.start_date_input, self.end_date_input],
                    layout=widgets.Layout(margin="0 0 10px 0"),
                ),
                # Action buttons
                self.create_action_layout(),
                self.status_output,
                self.code_display,
            ],
            layout=widgets.Layout(padding="20px"),
        )

        # Display layout based on use_sidecar setting
        if self.use_sidecar and self.sidecar is not None:
            # Display in sidecar
            self.sidecar.clear_output()
            with self.sidecar:
                display(layout)
        else:
            # Display in persistent output cell widget
            self.cell_output.clear_output()
            with self.cell_output:
                display(layout)

    def register_event_handlers(self):
        self.model_name_input.observe(self.on_modelname_change, names="value")
        self.model_universe_dropdown.observe(self.on_modelname_change, names="value")
        self.submit_button.on_click(self.on_submit)
        self.cancel_button.on_click(self.on_cancel)
        self.refresh_button.on_click(self.on_refresh)
        self.position_button.on_click(self.on_position_click)
        self.simulation_button.on_click(self.on_simulation_click)

    def create_title_widget(self) -> widgets.HTML:
        return widgets.HTML(
            value="<h1 style='text-align:center;'>Submission Dashboard</h1>"
        )

    def create_code_display_widget(self) -> widgets.HTML:
        code_display = widgets.HTML()
        self.update_code_display(code_display, "")
        return code_display

    def create_input_widgets(self) -> Tuple[widgets.Text, widgets.Dropdown]:
        modelname_input = widgets.Text(
            value=self.default_modelname,
            description="Model Name",
            placeholder="eg. directory/name",
            layout=widgets.Layout(width="auto"),
        )
        model_universe_dropdown = widgets.Dropdown(
            options=AVAILABLE_MARKETS,
            value=self.default_model_universe,
            description="Universe",
            layout=widgets.Layout(width="auto"),
        )
        return modelname_input, model_universe_dropdown

    def create_action_widgets(
        self,
    ) -> Tuple[
        widgets.Button,
        widgets.Button,
        widgets.Button,
        widgets.Button,
        widgets.Button,
        widgets.IntProgress,
    ]:
        button_layout = widgets.Layout(width="auto", margin="0 5px")
        submit_button = widgets.Button(
            description="Submit",
            button_style="primary",
            layout=button_layout,
        )
        cancel_button = widgets.Button(
            description="Close",
            button_style="danger",
            layout=button_layout,
        )
        position_button = widgets.Button(
            description="Position",
            button_style="info",
            layout=button_layout,
        )

        simulation_button = widgets.Button(
            description="Simulation",
            button_style="info",
            layout=button_layout,
        )

        refresh_button = widgets.Button(
            description="Clear",
            button_style="warning",
            layout=button_layout,
        )

        progress = widgets.IntProgress(
            value=0,
            min=0,
            max=100,
            description="Loading",
            bar_style="info",
            orientation="horizontal",
            layout=widgets.Layout(width="100%", margin="0"),
        )

        for button in [
            submit_button,
            cancel_button,
            position_button,
            simulation_button,
        ]:
            button.add_class("widget-button")

        return (
            submit_button,
            cancel_button,
            position_button,
            simulation_button,
            refresh_button,
            progress,
        )

    def create_action_layout(self) -> widgets.VBox:
        button_box = widgets.HBox(
            [
                self.submit_button,
                self.position_button,
                self.simulation_button,
                self.refresh_button,
                self.cancel_button,
            ],
            layout=widgets.Layout(
                justify_content="flex-start", align_items="center", margin="0"
            ),
        )
        return widgets.VBox(
            [button_box, self.progress],
            layout=widgets.Layout(margin="0"),
        )

    def on_modelname_change(self, change):
        self.update_info_display()

    def colored_print(self, text: str, color: str):
        if isinstance(text, str):
            formatted_text = text.replace("\n", "<br>").replace(
                " ", "&nbsp;"
            )  # 줄바꿈과 공백을 HTML에 맞게 변경
        else:
            formatted_text = str(text)
        with self.status_output:
            display(HTML(f"<pre style='color: {color};'>{formatted_text}</pre>"))

    def update_info_display(self):
        modelname = self.model_name_input.value

        self.status_output.clear_output(wait=True)
        if (
            modelname.startswith("/")
            or " " in modelname
            or "." in modelname
            or modelname.strip() == ""
        ):
            self.colored_print(
                "Error: Model name cannot start with '/' or contain spaces or '.'.",
                "red",
            )
            self.submit_button.disabled = True
            self.position_button.disabled = True
            self.simulation_button.disabled = True
        else:
            output_path = os.path.join(os.getcwd(), modelname, self.model_file_name)
            self.colored_print(f"Model will be saved to: {output_path}", "green")
            self.submit_button.disabled = False
            self.position_button.disabled = False
            self.simulation_button.disabled = False

        self.update_code_display(
            self.code_display,
            (
                output_path + f" ({self.model_type.lower()})"
                if "output_path" in locals()
                else ""
            ),
        )

    def update_code_display(self, code_display: widgets.HTML, file_path: str):
        formatter = HtmlFormatter(style="monokai")
        highlighted_code = highlight(self.model_cell.source, PythonLexer(), formatter)

        style = (
            MAC_STYLE + "<style>" + formatter.get_style_defs(".highlight") + "</style>"
        )
        html_content = f"""
        {style}
        <div class="mac-window" style="margin-top: 20px;">
            <div class="mac-titlebar">
                <div class="mac-buttons">
                    <div class="mac-button mac-close"></div>
                    <div class="mac-button mac-minimize"></div>
                    <div class="mac-button mac-zoom"></div>
                </div>
                <div class="mac-title" style="text-align: center; color: #fff; padding: 5px;">
                    {" " + file_path}
                </div>
            </div>
            <div class="mac-content" style="padding: 10px;">
                {highlighted_code}
            </div>
        </div>
        """
        code_display.value = html_content

    def submit(self, model_name=None, model_universe=None, gpu=None, bypass_validate=None, ignore_local_validation=None, submission_start_date=None, benchmark=None, insample=None):
        self.reinitialize(
            model_name=model_name,
            model_universe=model_universe,
            gpu=gpu,
            bypass_validate=bypass_validate,
            ignore_local_validation=ignore_local_validation,
            submission_start_date=submission_start_date,
            benchmark=benchmark,
            insample=insample
        )
        with self.status_output:
            try:
                print("Submission preparation...")
                self.save_model_and_load_instance()
                self.submit_model()
            except Exception as e:
                self.handle_error("Submission", e, raise_error=True)

    def get_position(self, start_date, end_date):
        self.reinitialize(start_date=start_date, end_date=end_date)
        with self.status_output:
            try:
                self.validate_dates()
                print(
                    f"Getting position for period: {self.start_date_input.value} to {self.end_date_input.value}"
                )
                self.save_model_and_load_instance()
                self.get_and_validate_position()
                return self.position
            except Exception as e:
                self.handle_error("Position Validation", e, raise_error=True)

    def get_simulation(self, start_date, end_date):
        self.reinitialize(start_date=start_date, end_date=end_date)
        with self.status_output:
            try:
                self.validate_dates()
                print(
                    f"Running simulation for period: {self.start_date_input.value} to {self.end_date_input.value}"
                )
                self.save_model_and_load_instance()
                self.get_and_validate_position()
                self.run_simulation()
                print("Simulation completed successfully.")
                return self.simulation_result
            except Exception as e:
                self.handle_error("Simulation", e, raise_error=True)

    def on_position_click(self, b: Any) -> None:
        self.status_output.clear_output(wait=True)
        self.progress.value = 10
        self.progress.bar_style = "info"
        self._run_position_task()

    def _run_position_task(self) -> None:
        """Execute position task with progress updates."""
        try:
            with self.status_output:
                self.validate_dates()
                self.progress.value = 15
                print(
                    f"Getting position for period: {self.start_date_input.value} to {self.end_date_input.value}"
                )
                self.progress.value = 20
                self.save_model_and_load_instance()
                self.progress.value = 40
                self.get_and_validate_position()
                self.progress.value = 90
                self.progress.value = 100
                self.progress.bar_style = "success"
        except Exception as e:
            self.handle_error("Position", e)

    def on_submit(self, b: Any) -> None:
        self.status_output.clear_output(wait=True)
        self.progress.value = 5
        self.progress.bar_style = "info"
        self.set_button_states(submit_disabled=True, cancel_disabled=True)
        self._run_submit_task()
        self.set_button_states(submit_disabled=False, cancel_disabled=False)

    def _run_submit_task(self) -> None:
        """Execute submit task with progress updates."""
        try:
            with self.status_output:
                print("Submission preparation...")
                self.progress.value = 10
                self.save_model_and_load_instance()
                self.progress.value = 30
                self._prepare_model_info()
                self.progress.value = 40

                if self.check_name_exist():
                    self.show_overwrite_dialog()
                else:
                    self._execute_submission()
        except Exception as e:
            self.handle_error("Submission", e)

    def _validate_insample_format(self, value: str) -> bool:
        """Validate insample format: must be digits followed by 'day' (e.g., '20day')"""
        if not value:
            return True
        pattern = r'^\d+day$'
        return bool(re.match(pattern, value))

    def _prepare_model_info(self) -> None:
        """Prepare model info for submission."""
        self.model_info = get_model_info(
            self.model_universe_dropdown.value,
            self.model_type,
        )
        self.model_info["bypass_validate"] = self.bypass_validate_checkbox.value
        self.model_info["gpu"] = self.gpu_checkbox.value

        # Validate mutual exclusivity of start date and insample
        start_date_value = self.submission_start_date_input.value.strip()
        insample_value = self.insample_input.value.strip()

        if start_date_value and insample_value:
            raise ValueError("Start Date and Insample are mutually exclusive. Please use only one of these options.")

        if start_date_value:
            try:
                self.model_info["start"] = int(start_date_value)
            except ValueError:
                raise ValueError(f"Invalid start date format: {start_date_value}. Expected YYYYMMDD as integer.")

        if insample_value:
            if not self._validate_insample_format(insample_value):
                raise ValueError(f"Invalid insample format: {insample_value}. Expected format: <number>day (e.g., '20day', '1day')")
            self.model_info["insample"] = insample_value

        if self.benchmark_input.value.strip():
            self.model_info["simulation_info"]["benchmark"] = self.benchmark_input.value.strip()

        with self.status_output:
            print(
                f"Name: {self.model_name_input.value}, Universe: {self.model_universe_dropdown.value}, Type: {self.model_type.lower()}"
            )
            if self.gpu_checkbox.value:
                print("GPU: Enabled")
            if self.bypass_validate_checkbox.value:
                print("Bypass Validate: Enabled")
            if self.ignore_local_validation_checkbox.value:
                print("Ignore Local Validation: Enabled")
            if start_date_value:
                print(f"Start Date: {start_date_value}")
            if insample_value:
                print(f"Insample: {insample_value}")
            if self.benchmark_input.value.strip():
                print(f"Benchmark: {self.benchmark_input.value.strip()}")

    def _execute_submission(self) -> None:
        """Execute the actual submission with progress updates."""
        try:
            with self.status_output:
                print("Submission started...")
                self.progress.value = 50

                if not self.ignore_local_validation_checkbox.value:
                    validator = ValidationHelper(
                        model_path=self.model_name_input.value, model_info=self.model_info
                    )
                    validator.validate()
                    print("Local validation passed.")
                else:
                    print("Local validation skipped.")

                self.progress.value = 70

                submit_result = submit_model(
                    model_info=self.model_info,
                    output_directory=self.model_name_input.value,
                    docker_submit=True,
                    staging=False,
                )

                self.progress.value = 90

                if submit_result is None:
                    raise RuntimeError("Error submitting the model.")
                else:
                    self.progress.value = 100
                    self.progress.bar_style = "success"
                    print("Submission completed!")
                    print(f"Model ID: {submit_result.result['identity_name']}")
                    if not self.bypass_validate_checkbox.value:
                        print("Validation is in progress on the server.")
                    else:
                        print("Server validation bypassed.")
                    display(
                        HTML(
                            f'<a href="{submit_result.s3_url}" target="_blank">Validation URL</a>'
                        )
                    )
        except Exception as e:
            self.handle_error("Submission", e)

    def on_simulation_click(self, b: Any) -> None:
        self.status_output.clear_output(wait=True)
        self.progress.value = 10
        self.progress.bar_style = "info"
        self._run_simulation_task()

    def _run_simulation_task(self) -> None:
        """Execute simulation task with progress updates."""
        try:
            with self.status_output:
                self.validate_dates()
                self.progress.value = 10
                print(
                    f"Running simulation for period: {self.start_date_input.value} to {self.end_date_input.value}"
                )
                self.progress.value = 15
                self.save_model_and_load_instance()
                self.progress.value = 25
                self.get_and_validate_position()
                self.progress.value = 75
                self.run_simulation()
                self.progress.value = 90
                print("Simulation completed successfully.")
                self.progress.value = 100
                self.progress.bar_style = "success"
        except Exception as e:
            self.handle_error("Simulation", e)

    def reinitialize(
        self,
        start_date=None,
        end_date=None,
        model_name=None,
        model_universe=None,
        gpu=None,
        bypass_validate=None,
        ignore_local_validation=None,
        submission_start_date=None,
        benchmark=None,
        insample=None,
    ) -> None:
        # Stop any running progress animation before reinitializing UI
        try:
            self.stop_progress()
        except Exception:
            pass
        self.__init__(
            start_date if start_date is not None else self.start_date_input.value,
            end_date if end_date is not None else self.end_date_input.value,
            model_name if model_name is not None else self.model_name_input.value,
            (
                model_universe
                if model_universe is not None
                else self.model_universe_dropdown.value
            ),
            gpu if gpu is not None else self.gpu_checkbox.value,
            bypass_validate if bypass_validate is not None else self.bypass_validate_checkbox.value,
            ignore_local_validation if ignore_local_validation is not None else self.ignore_local_validation_checkbox.value,
            submission_start_date if submission_start_date is not None else self.submission_start_date_input.value,
            benchmark if benchmark is not None else self.benchmark_input.value,
            insample if insample is not None else self.insample_input.value,
            use_sidecar=self.use_sidecar,
        )
        self.status_output.clear_output()

    def on_refresh(self, b: Any) -> None:
        self.reinitialize()

    def validate_dates(self) -> None:
        start_date = self.start_date_input.value
        end_date = self.end_date_input.value
        if not start_date or not end_date:
            raise ValueError("Please enter both start and end dates.")
        if start_date > end_date:
            raise ValueError("Start date must be before end date.")

    def get_and_validate_position(self) -> None:
        self.position = self.model_instance.get(
            self.start_date_input.value, self.end_date_input.value
        )
        print("Position retrieved successfully.")
        print(self.position.sum(axis=1).tail())
        self.model_info = get_model_info(
            self.model_universe_dropdown.value, self.model_type
        )
        validator = ValidationHelper(
            model_path=self.model_name_input.value, model_info=self.model_info
        )
        validator.validate()

    def run_simulation(self) -> None:
        from finter.backtest.simulator import Simulator

        simulator = Simulator(self.model_universe_dropdown.value)
        results = simulator.run(
            self.position,
            start=self.start_date_input.value,
            end=self.end_date_input.value,
        )
        summary = results.summary
        self.simulation_result = summary
        self.plot_nav(summary)

    def plot_nav(self, summary: Any) -> None:
        import plotly.graph_objs as go

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=summary["nav"].index,
                y=summary["nav"].values,
                mode="lines",
                name="NAV",
            )
        )
        fig.update_layout(
            title="Simulation Results: NAV", xaxis_title="Date", yaxis_title="NAV"
        )
        display(fig)

    def check_name_exist(self) -> bool:
        return name_exist(
            self.model_type,
            self.model_universe_dropdown.value,
            self.model_name_input.value.split("/")[-1],
        )

    def save_model_and_load_instance(self):
        self.output_path = os.path.join(
            os.getcwd(), self.model_name_input.value, self.model_file_name
        )

        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        self.write_notebook(self.output_path)
        with self.status_output:
            print(f"Notebook saved to {self.output_path}")

        path_manager = FileManager()
        path_manager.clear_paths()
        self.model_instance = load_model_instance(self.output_path, self.model_type)
        path_manager.copy_files_to(self.model_name_input.value)

    def submit_model(self):
        self.model_info = get_model_info(
            self.model_universe_dropdown.value,
            self.model_type,
        )

        # Add submission options to model_info
        self.model_info["bypass_validate"] = self.bypass_validate_checkbox.value
        self.model_info["gpu"] = self.gpu_checkbox.value

        # Validate mutual exclusivity of start date and insample
        start_date_value = self.submission_start_date_input.value.strip()
        insample_value = self.insample_input.value.strip()

        if start_date_value and insample_value:
            raise ValueError("Start Date and Insample are mutually exclusive. Please use only one of these options.")

        # Add optional submission start date (convert to int)
        if start_date_value:
            try:
                self.model_info["start"] = int(start_date_value)
            except ValueError:
                raise ValueError(f"Invalid start date format: {start_date_value}. Expected YYYYMMDD as integer.")

        # Add optional insample
        if insample_value:
            if not self._validate_insample_format(insample_value):
                raise ValueError(f"Invalid insample format: {insample_value}. Expected format: <number>day (e.g., '20day', '1day')")
            self.model_info["insample"] = insample_value

        # Add optional benchmark
        if self.benchmark_input.value.strip():
            self.model_info["simulation_info"]["benchmark"] = self.benchmark_input.value.strip()

        with self.status_output:
            print(
                f"Name: {self.model_name_input.value}, Universe: {self.model_universe_dropdown.value}, Type: {self.model_type.lower()}"
            )
            if self.gpu_checkbox.value:
                print("GPU: Enabled")
            if self.bypass_validate_checkbox.value:
                print("Bypass Validate: Enabled")
            if self.ignore_local_validation_checkbox.value:
                print("Ignore Local Validation: Enabled")
            if start_date_value:
                print(f"Start Date: {start_date_value}")
            if insample_value:
                print(f"Insample: {insample_value}")
            if self.benchmark_input.value.strip():
                print(f"Benchmark: {self.benchmark_input.value.strip()}")

        if self.check_name_exist():
            # if self.overwrite:
            #     self.colored_print("Warning: Overwriting existing model.", "orange")
            #     self.proceed_with_submission()
            # else:
            self.show_overwrite_dialog()
        else:
            self.proceed_with_submission()

    def show_overwrite_dialog(self):
        with self.status_output:
            print("Model name already exists. Do you want to overwrite?")
            overwrite_button = widgets.Button(
                description="Overwrite", button_style="warning"
            )
            cancel_button = widgets.Button(description="Close", button_style="danger")

            overwrite_button.on_click(lambda _: self._execute_submission())
            cancel_button.on_click(lambda _: self.cancel_submission())

            display(widgets.HBox([overwrite_button, cancel_button]))
            self.progress.value = 45
            self.progress.bar_style = "warning"

    def proceed_with_submission(self):
        """Legacy method - redirects to _execute_submission for backwards compatibility."""
        self._execute_submission()

    def cancel_submission(self):
        self.status_output.clear_output()
        self.colored_print("Submission cancelled.", "orange")

    def handle_error(self, process: str, error: Exception, raise_error: bool = False):
        try:
            self.stop_progress()
        except Exception:
            pass
        self.progress.bar_style = "danger"
        self.progress.value = 100
        self.colored_print(f"{process} failed: {str(error)}", "red")
        if raise_error:
            raise

    def on_cancel(self, b):
        if self.sidecar is not None:
            self.sidecar.close()
        # with self.status_output:
        # clear_output(wait=True)
        # self.colored_print("Submission cancelled.", "orange")

    def set_button_states(self, submit_disabled: bool, cancel_disabled: bool):
        self.submit_button.disabled = submit_disabled
        self.cancel_button.disabled = cancel_disabled

    def start_progress(self):
        # Stop any previous animation before starting a new one
        try:
            self.stop_progress()
        except Exception:
            pass

        self.progress.value = 0
        self.progress.bar_style = "info"

        self._progress_stop_event = threading.Event()

        def set_value_safely(new_value: int):
            try:
                self.progress.value = new_value
            except Exception:
                # Ignore UI update errors (e.g., kernel teardown)
                pass

        current_value = 0
        direction = 1

        def progress_animation():
            nonlocal current_value, direction
            # If we cannot access the main loop, avoid background UI updates
            if self._loop is None:
                return
            while not self._progress_stop_event.is_set():
                if current_value > 95:
                    current_value = 100
                    try:
                        self._loop.call_soon_threadsafe(set_value_safely, current_value)
                    except Exception:
                        pass
                    break

                if current_value >= 90:
                    direction = -1
                elif current_value <= 80:
                    direction = 1

                current_value += direction
                try:
                    self._loop.call_soon_threadsafe(set_value_safely, current_value)
                except Exception:
                    pass
                time.sleep(0.1)

        self._progress_thread = threading.Thread(target=progress_animation, daemon=True)
        self._progress_thread.start()

    def stop_progress(self):
        # Signal the animation thread to stop and wait briefly
        if hasattr(self, "_progress_stop_event") and self._progress_stop_event is not None:
            self._progress_stop_event.set()
        if hasattr(self, "_progress_thread") and self._progress_thread is not None:
            try:
                if self._progress_thread.is_alive():
                    self._progress_thread.join(timeout=0.2)
            except Exception:
                pass
