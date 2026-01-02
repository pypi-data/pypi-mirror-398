from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from pandas.core.frame import DataFrame as PandasDataFrame

from dijkies.evaluate import EvaluationFramework
from dijkies.executors import BacktestExchangeAssetClient
from dijkies.performance import PerformanceInformationRow
from dijkies.exceptions import (
    DataTimeWindowShorterThanSuggestedAnalysisWindowError,
    InvalidExchangeAssetClientError,
    InvalidTypeForTimeColumnError,
    MissingOHLCVColumnsError,
    TimeColumnNotDefinedError,
)
from dijkies.strategy import Strategy


class Backtester:
    def __init__(
        self,
        evaluation: Optional[EvaluationFramework] = None,
    ):
        self.evaluation = evaluation

    @staticmethod
    def get_analysis_df(
        data: PandasDataFrame, current_time: datetime, look_back_in_min: int
    ) -> PandasDataFrame:
        start_analysis_df = current_time - timedelta(minutes=look_back_in_min)

        analysis_df = data.loc[
            (data.time >= start_analysis_df) & (data.time <= current_time)
        ]

        return analysis_df

    def simulate(
        self,
        data: PandasDataFrame,
        strategy: Strategy,
    ) -> PandasDataFrame:
        """
        This method runs the backtest. It expects data, this should have the following properties:
        """

        # validate args

        if "time" not in data.columns:
            raise TimeColumnNotDefinedError()

        if not pd.api.types.is_datetime64_any_dtype(data.time):
            raise InvalidTypeForTimeColumnError()

        lookback_in_min = strategy.analysis_dataframe_size_in_minutes
        timespan_data_in_min = (data.time.max() - data.time.min()).total_seconds() / 60

        if lookback_in_min > timespan_data_in_min:
            raise DataTimeWindowShorterThanSuggestedAnalysisWindowError()

        if not {"open", "high", "low", "close", "volume"}.issubset(data.columns):
            raise MissingOHLCVColumnsError()

        if not isinstance(strategy.executor, BacktestExchangeAssetClient):
            raise InvalidExchangeAssetClientError()

        start_time = data.iloc[0].time + timedelta(minutes=lookback_in_min)
        simulation_df: PandasDataFrame = data.loc[data.time >= start_time]
        start_candle = simulation_df.iloc[0]
        start_value_in_quote = strategy.state.total_value_in_quote(start_candle.open)
        result = []

        for _, candle in simulation_df.iterrows():
            analysis_df = self.get_analysis_df(data, candle.time, lookback_in_min)
            strategy.executor.update_current_candle(candle)

            strategy.run(analysis_df)

            result.append(
                PerformanceInformationRow.from_objects(
                    candle, start_candle, strategy.state, start_value_in_quote
                )
            )

        return pd.DataFrame([r.dict() for r in result])

    def run(
        self,
        candle_df: PandasDataFrame,
        strategy: Strategy,
    ) -> PandasDataFrame:

        results = self.simulate(candle_df, strategy)
        if isinstance(self.evaluation, EvaluationFramework):
            self.evaluation.evaluate(results)

        return results
