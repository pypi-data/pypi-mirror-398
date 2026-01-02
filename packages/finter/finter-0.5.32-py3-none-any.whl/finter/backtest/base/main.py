from finter.backtest.base.variables import InputVars, SimulationVariables
from finter.backtest.config.config import SimulatorConfig
from finter.backtest.result.main import BacktestResult
from finter.settings import log_warning


class BaseBacktestor:
    def __init__(
        self,
        config: SimulatorConfig,
        input_vars: InputVars,
        results: list[str] = [],
    ):
        self.results = results

        self.frame = config.frame
        self.trade = config.trade
        self.execution = config.execution
        self.optional = config.optional
        self.cost = config.cost

        self.vars = SimulationVariables(input_vars, self.frame.shape)
        self.vars.initialize(self.trade.initial_cash)

        self._results = BacktestResult(self)

    def _clear_all_variables(self, clear_attrs=True):
        # cached_property로 이미 계산된 결과만 보존 (불필요한 재계산 방지)
        preserved = {}
        if hasattr(self._results, "__dict__"):
            results_dict = self._results.__dict__
            for attr_name in self.results:
                # __dict__에 이미 캐시되어 있으면 가져오기 (property 실행 방지)
                if attr_name in results_dict:
                    preserved[attr_name] = results_dict[attr_name]
                else:
                    # 캐시되지 않은 경우 계산 (EAFP 패턴)
                    try:
                        preserved[attr_name] = getattr(self._results, attr_name)
                    except AttributeError:
                        log_warning(
                            f"Attribute '{attr_name}' in results not found in self._results"
                        )

        if clear_attrs:
            # delattr 루프 대신 dict.clear() 사용 (O(n²) → O(n))
            self.__dict__.clear()

        # preserved attributes를 한 번에 복원
        self.__dict__.update(preserved)

    def run(self):
        raise NotImplementedError

    def run_step(self, i: int):
        raise NotImplementedError
