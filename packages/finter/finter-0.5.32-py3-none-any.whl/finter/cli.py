import os
import re

import click

from finter import __version__
from finter.framework_model.submission.config import get_model_info
from finter.framework_model.submission.helper_submission import submit_model
from finter.framework_model.validation import ValidationHelper


def validate_insample_format(ctx, param, value):
    """Validate insample format: must be digits followed by 'day' (e.g., '20day')"""
    if value is None:
        return value
    pattern = r'^\d+day$'
    if not re.match(pattern, value):
        raise click.BadParameter(
            click.style(
                "insample must be in format: <number>day (e.g., '20day', '1day')",
                fg="red"
            )
        )
    return value


@click.group()
@click.version_option(version=__version__, prog_name="finter")
def finter():
    """Finter CLI - A tool for submitting models with specific configurations."""
    pass


@finter.command()
@click.option(
    "--universe",
    required=True,
    type=click.Choice(
        [
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
        ],
        case_sensitive=False,
    ),
    help="The name of the universe (required).",
)
@click.option(
    "--gpu", required=False, is_flag=True, help="Whether to use GPU machine (optional)."
)
@click.option(
    "--custom-docker-file",
    required=False,
    is_flag=True,
    help="Whether to use custom docker file (optional). If not provided, an appropriate Dockerfile will be generated.",
)
@click.option(
    "--start",
    required=False,
    type=int,
    help="Start date for submission in YYYYMMDD format (optional). If not provided, the system will automatically calculate the start date during submission.",
)
@click.option(
    "--ignore-local-validation",
    required=False,
    is_flag=True,
    help="Ignore local validation (optional).",
)
@click.option(
    "--benchmark",
    required=False,
    type=str,
    help="Specify a benchmark model to use (optional). Must be an identity_name or universe name.",
)
@click.option(
    "--insample",
    required=False,
    type=str,
    callback=validate_insample_format,
    help="Specify a insample period in format <number>day (e.g., '20day'). Cannot be used with --start.",
)
@click.option(
    "--bypass-validate",
    required=False,
    is_flag=True,
    help="Bypass validation (optional).",
)
@click.option(
    "--image-tag",
    required=False,
    type=str,
    help="Base image tag to use for model submission environment (optional).",
)

@click.option(
    "--staging",
    required=False,
    is_flag=True,
    help="Whether to use staging environment (optional).",
)
@click.option(
    "--legacy",
    required=False,
    is_flag=True,
    help="Use legacy submission mode without Docker (deprecated).",
)
def submit(
    universe,
    gpu,
    custom_docker_file,
    start,
    ignore_local_validation,
    benchmark,
    insample,
    bypass_validate,
    image_tag,
    staging,
    legacy,
):
    current_dir = os.getcwd()
    click.echo(f"Current working directory: {current_dir}")

    model_alias = os.path.basename(current_dir)
    click.echo(f"Model alias: {model_alias}")

    model_files = [
        f for f in os.listdir(current_dir) if f in ["am.py", "pf.py", "ffd.py"]
    ]

    if len(model_files) != 1:
        click.echo(
            click.style(
                "Error: Exactly one model file (am.py, pf.py, ffd.py) must exist.",
                fg="red",
            ),
            err=True,
        )
        return

    model_file = model_files[0]

    model_type = {"am.py": "alpha", "pf.py": "portfolio", "ffd.py": "flexible_fund"}[
        model_file
    ]

    click.echo(f"Model type: {model_type}")

    venv_path = os.path.join(current_dir, ".venv")
    if os.path.exists(venv_path) and os.path.isdir(venv_path):
        click.echo(
            click.style(
                "Error: '.venv' directory exists in the submission directory. Virtual environment folders are not allowed for submission. Please either move your virtual environment to another location or delete it before submitting.",
                fg="red",
            ),
            err=True,
        )
        return

    
    click.echo(f"Submitting model: {model_alias}")

    # Validate mutually exclusive options
    if custom_docker_file and image_tag:
        click.echo(
            click.style(
                "Error: --custom-docker-file and --image-tag are mutually exclusive. "
                "Please use only one of these options.",
                fg="red",
            ),
            err=True,
        )
        return

    # Validate start and insample are mutually exclusive
    if start and insample:
        click.echo(
            click.style(
                "Error: --start and --insample are mutually exclusive. "
                "Please use only one of these options.",
                fg="red",
            ),
            err=True,
        )
        return

    docker_file = os.path.join(current_dir, "Dockerfile")

    if custom_docker_file:
        if not os.path.exists(docker_file):
            click.echo(
                click.style(
                    "Error: 'Dockerfile' file not found. Please ensure it exists in the current directory.",
                    fg="red",
                ),
                err=True,
            )
            return
    else:
        if os.path.exists(docker_file):
            click.echo(
                click.style(
                    "Error: 'Dockerfile' file found in the current directory. Use --custom-docker-file to submit the model with your Dockerfile.",
                    fg="red",
                ),
                err=True,
            )
            return

    model_info = get_model_info(universe, model_type)

    if bypass_validate:
        model_info["bypass_validate"] = True
    else:
        model_info["bypass_validate"] = False

    model_info["gpu"] = gpu
    model_info["finter_version"] = __version__
    if start:
        model_info["start"] = start
    if benchmark:
        model_info["simulation_info"]["benchmark"] = benchmark
    if image_tag:
        model_info["image_tag"] = image_tag
    if insample:
        model_info["insample"] = insample

    try:
        if not ignore_local_validation:
            validator = ValidationHelper(
                model_path=current_dir, model_info=model_info, start_date=start
            )
            validator.validate()
        else:
            click.echo("Local validation skipped.")

        if legacy:
            click.echo(
                "Warning: Using legacy submission mode without Docker (deprecated)"
            )

        submit_result = submit_model(
            model_info=model_info,
            output_directory=current_dir,
            docker_submit=not legacy,
            staging=staging,
            model_nickname=model_alias,
        )

        if submit_result is None:
            click.echo(
                click.style(
                    "Error: Submission failed. Please check the error message above.",
                    fg="red",
                    bold=True
                ),
                err=True,
            )
            return

        click.echo(
            "Validation URL: "
            + click.style(submit_result.s3_url, fg="blue", underline=True)
        )
    except Exception as e:
        click.echo(
            click.style(f"Error submitting model: {e}", fg="red"),
            err=True,
        )
        return


@finter.command()
@click.option(
    "--path", type=str, required=False, help="Path in format 'folder/model_alias'"
)
def start(path):
    """Create a new model directory with template files.

    Usage:
        finter start --path folder/model_alias
        finter start  # Interactive mode
    """
    if not path:
        click.echo(
            "Interactive mode (alternatively, you can use: finter start --path folder/model_alias)"
        )
        click.echo("Example: models/my_alpha_model")
        click.echo("-" * 50)

        path = click.prompt("Enter path (e.g., 'models/my_alpha_model')", type=str)

    # Create the full path and get model alias
    full_path = os.path.normpath(os.path.join(os.getcwd(), path))

    # 폴더가 이미 존재하는 경우 경고 메시지 출력
    if os.path.exists(full_path):
        if os.listdir(full_path):
            click.echo(
                click.style(
                    f"Error: Directory '{full_path}' already exists.", fg="red"
                ),
                err=True,
            )
            click.echo("Please remove the directory manually and try again.")
            return

    try:
        # Create directories if they don't exist
        os.makedirs(full_path, exist_ok=True)

        # Create am.py with template content
        am_file = os.path.join(full_path, "am.py")
        with open(am_file, "w") as f:
            f.write('''from finter import BaseAlpha
from finter.data import ContentFactory
from finter.modeling.calendar import DateConverter


class Alpha(BaseAlpha):
    """
    Alpha model template function.

    Args:
        start (int): Start date in YYYYMMDD format
        end (int): End date in YYYYMMDD format

    Returns:
        pd.DataFrame: Predictions position dataframe
    """

    universe = "kr_stock"

    # Abstract method
    def get(self, start, end):
        lookback_days = 365
        pre_start = DateConverter.get_pre_start(start, lookback_days)

        cf = ContentFactory(self.universe, pre_start, end)
        price = cf.get_df("price_close")

        rank = price.rolling(21).mean().rank(pct=True, axis=1)

        selected = rank[rank > 0.8]

        position = selected.div(selected.sum(axis=1), axis=0) * 1e8
        position = position.shift()

        return position.loc[str(start) : str(end)]

    # Free method
    def run(self, start, end):
        return self.backtest(self.universe, start, end)


if __name__ == "__main__":
    alpha = Alpha()

    start, end = 20200101, 20240101
    results = alpha.run(start, end)
    results.nav.plot()

    # position = alpha.get(start, end)
''')

        click.echo(f"\nSuccessfully created model template at: {full_path}")
        click.echo("Created files:")
        click.echo(f"  - {am_file}")

    except Exception as e:
        click.echo(
            click.style(f"Error creating model template: {e}", fg="red"),
            err=True,
        )
        return


if __name__ == "__main__":
    finter()
