import logging
import os
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Union

import matplotlib.pyplot as plt
import mlflow
import pandas as pd
from pandas.core.frame import DataFrame as PandasDataFrame

from dijkies.performance import Metric


class EvaluationFramework(ABC):
    @abstractmethod
    def evaluate(self, performance_results: PandasDataFrame) -> None:
        pass


class MLFlowEvaluator(ABC):
    @abstractmethod
    def evaluate(self, performance_results: PandasDataFrame) -> None:
        pass


class MLFlowEvaluationFramework(EvaluationFramework):
    def __init__(
        self,
        evaluators: list[MLFlowEvaluator],
        experiment_name: str,
        logger: logging.Logger,
        strategy_parameters: Optional[dict[str, Union[int, str, float, bool]]],
        log_dataset: bool = False,
    ) -> None:
        self.evaluators = evaluators
        self.logger = logger
        self.experiment_name = experiment_name
        self.log_dataset = log_dataset
        self.strategy_parameters = strategy_parameters

    def evaluate(self, performance_results: PandasDataFrame) -> None:
        mlflow.set_experiment(self.experiment_name)
        # for results:
        # poetry run mlflow server --host 127.0.0.1 --port 8080

        run_name = "run__" + datetime.now(tz=timezone.utc).strftime("%Y_%m_%d_%H_%M%Z")

        with mlflow.start_run(run_name=run_name) as run:
            run_id = run.info.run_id
            self.logger.info("Run created: " + run_id)
            if self.log_dataset:
                dataset = mlflow.data.from_pandas(
                    performance_results, source="local", name="training_data"
                )
                mlflow.log_input(dataset, context="training")
                mlflow.log_params(self.strategy_parameters)
                with tempfile.TemporaryDirectory() as tmpdir:
                    file_path = os.path.join(tmpdir, "data.csv")
                    performance_results.to_csv(file_path, index=False)
                    mlflow.log_artifact(file_path)

            [
                evaluator.evaluate(performance_results) for evaluator in self.evaluators
            ]  # type: ignore


class MLFlowOverallEvaluator(MLFlowEvaluator):
    def __init__(self, metrics: list[Metric], logger: logging.Logger) -> None:
        self.metrics = metrics
        self.logger = logger

    def log_metrics(self, performance_results: PandasDataFrame) -> None:
        for metric in self.metrics:
            mlflow.log_metric(
                "strategy_" + metric.metric_name,
                round(metric.calculate(performance_results.total_value_strategy), 2),
            )
            mlflow.log_metric(
                "hodl_" + metric.metric_name,
                round(metric.calculate(performance_results.total_value_hodl), 2),
            )

    @staticmethod
    def plot_fee(performance_results: PandasDataFrame) -> None:
        plt.figure(figsize=(8, 5))
        plt.plot(
            performance_results.candle_time,
            performance_results.total_fee_paid,
            color="blue",
            label="fee",
        )
        plt.xlabel("Time")
        plt.xticks(rotation=45)
        plt.ylabel("fee paid in €")
        plt.title("total transaction fee paid to Exchange")
        plt.grid(True)
        plt.legend()

        # Log figure directly to MLflow
        mlflow.log_figure(plt.gcf(), "total_fee_paid.png")

        plt.close()  # free memory

    @staticmethod
    def plot_balance_fractions(performance_results: PandasDataFrame) -> None:
        perc_in_quote = (
            performance_results.balance_total_quote
            / performance_results.total_value_strategy
        )
        perc_in_base = (
            performance_results.balance_total_base
            / performance_results.total_value_strategy
            * performance_results.candle_close
        )

        plt.figure(figsize=(8, 5))
        plt.plot(
            performance_results.candle_time,
            perc_in_quote,
            color="blue",
            label="percentage value in quote",
        )
        plt.plot(
            performance_results.candle_time,
            perc_in_base,
            color="red",
            label="percentage value in base",
        )
        plt.xlabel("Time")
        plt.xticks(rotation=45)
        plt.ylabel("fraction")
        plt.title("fraction of total value in quote")
        plt.grid(True)
        plt.legend()

        # Log figure directly to MLflow
        mlflow.log_figure(plt.gcf(), "balance_fractions.png")

        plt.close()  # free memory

    @staticmethod
    def plot_strategy_vs_hodl(performance_results: PandasDataFrame) -> None:
        plt.figure(figsize=(8, 5))
        plt.plot(
            performance_results.candle_time,
            performance_results.total_value_strategy,
            color="blue",
            label="strategy",
        )
        plt.plot(
            performance_results.candle_time,
            performance_results.total_value_hodl,
            color="red",
            label="hodl",
        )
        plt.xlabel("Time")
        plt.xticks(rotation=45)
        plt.ylabel("Value")
        plt.title("strategy vs. hodl")
        plt.grid(True)
        plt.legend()

        # Log figure directly to MLflow
        mlflow.log_figure(plt.gcf(), "overal_result.png")

        plt.close()  # free memory

    def plot_results(self, performance_results: PandasDataFrame) -> None:
        self.plot_strategy_vs_hodl(performance_results)
        self.plot_fee(performance_results)
        self.plot_balance_fractions(performance_results)

    def evaluate(self, performance_results: PandasDataFrame) -> None:
        self.log_metrics(performance_results)
        self.plot_results(performance_results)


class MLFlowSliceEvaluator(MLFlowEvaluator):
    def __init__(
        self, window_size_in_min: int, metrics: list[Metric], logger: logging.Logger
    ) -> None:
        self.window_size_in_min = window_size_in_min
        self.metrics = metrics
        self.logger = logger

    def results_window_slicer(self, results: PandasDataFrame) -> PandasDataFrame:
        candle_interval_in_minutes = (
            results.iloc[1].candle_time - results.iloc[0].candle_time
        ).total_seconds() / 60
        window_size = self.window_size_in_min / candle_interval_in_minutes

        evaluation = []

        for sub_result in [
            results.loc[i : i + window_size]
            for i in range(len(results) - (int(window_size) + 1))
        ]:
            row = {}
            for metric in self.metrics:
                row["strategy_" + metric.metric_name] = metric.calculate(
                    sub_result.total_value_strategy
                )
                row["hodl_" + metric.metric_name] = metric.calculate(
                    sub_result.total_value_hodl
                )
            evaluation.append(row)

        return pd.DataFrame(evaluation)

    def plot_results(self, slicer_results: PandasDataFrame) -> None:
        for col in slicer_results.columns:
            self.logger.info(f"create plot {col}")
            plt.figure(figsize=(8, 5))
            plt.hist(slicer_results[col])
            plt.title(f"Column: {col}")
            plt.xlabel(col)
            plt.grid(True)

            # Log figure directly to MLflow
            mlflow.log_figure(plt.gcf(), f"{col}.png")

            plt.close()  # free memory

    def log_metrics(self, slicer_results: PandasDataFrame) -> None:
        for col in slicer_results.columns:
            self.logger.info(f"compute metrics for {col}")
            mlflow.log_metric(f"{col}_mean", round(slicer_results[col].mean(), 3))
            mlflow.log_metric(f"{col}_std", round(slicer_results[col].std(), 3))

    def evaluate(self, performance_results: PandasDataFrame) -> None:
        slicer_results = self.results_window_slicer(performance_results)
        self.log_metrics(slicer_results)
        self.plot_results(slicer_results)
