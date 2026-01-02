from abc import ABC, abstractmethod

import pandas as pd
from pandas.core.frame import DataFrame as PandasDataFrame


class DataPipeline(ABC):
    @abstractmethod
    def run(self) -> PandasDataFrame:
        pass


class NoDataPipeline(ABC):
    def run(self) -> PandasDataFrame:
        return pd.DataFrame({})
