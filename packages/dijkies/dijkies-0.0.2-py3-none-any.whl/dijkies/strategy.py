import inspect
from abc import ABC, abstractmethod

from pandas.core.frame import DataFrame as PandasDataFrame

from dijkies.executors import ExchangeAssetClient
from dijkies.data_pipeline import DataPipeline


class Strategy(ABC):
    def __init__(
        self,
        executor: ExchangeAssetClient,
        data_pipeline: DataPipeline
    ) -> None:
        self.executor = executor
        self.state = self.executor.state
        self.data_pipeline = data_pipeline

    @abstractmethod
    def execute(self, data: PandasDataFrame) -> None:
        pass

    def run(self, data: PandasDataFrame) -> None:
        self.executor.update_state()
        self.execute(data)

    @classmethod
    def _get_strategy_params(cls) -> list[str]:
        subclass_sig = inspect.signature(cls.__init__)
        base_sig = inspect.signature(Strategy.__init__)

        subclass_params = {
            name: p for name, p in subclass_sig.parameters.items() if name != "self"
        }
        base_params = {
            name: p for name, p in base_sig.parameters.items() if name != "self"
        }

        unique_params = {
            name: p for name, p in subclass_params.items() if name not in base_params
        }

        return list(unique_params.keys())

    def params_to_json(self):
        params = self._get_strategy_params()
        return {p: getattr(self, p) for p in params}

    @property
    @abstractmethod
    def analysis_dataframe_size_in_minutes(self) -> int:
        pass
