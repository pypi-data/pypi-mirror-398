import os
import json
import pickle

from abc import ABC, abstractmethod

from dijkies.strategy import Strategy
from dijkies.executors import State
from dijkies.credentials import Credentials
from dijkies.executors import BitvavoExchangeAssetClient
from dijkies.logger import get_logger


class StrategyRepository(ABC):
    @abstractmethod
    def store(self, strategy: Strategy, id: str) -> None:
        pass

    @abstractmethod
    def store_state(self, state: State, id: str) -> None:
        pass

    @abstractmethod
    def read(self, id: str) -> Strategy:
        pass

    @abstractmethod
    def read_state(self, id: str) -> State:
        pass


class LocalStrategyRepository(StrategyRepository):
    def __init__(self, root_directory: str) -> None:
        self.root_directory = root_directory

    def store(self, strategy: Strategy, id: str):
        path = os.path.join(self.root_directory, id + ".pkl")
        with open(path, "wb") as file:
            pickle.dump(strategy, file)

    def store_state(self, state: State, id: str) -> None:
        path = os.path.join(self.root_directory, "state_" + id, ".json")
        with open(path, "w") as file:
            json.dump(state, file)

    def read(self, id: str) -> Strategy:
        path = os.path.join(self.root_directory, id + ".pkl")
        with open(path, "rb") as file:
            strategy = pickle.load(file)
        return strategy

    def read_state(self, id: str) -> State:
        path = os.path.join(self.root_directory, "state_" + id, ".json")
        with open(path, "r") as file:
            state = json.load(file)
        return state


class CredentialsRepository(ABC):
    @abstractmethod
    def get_api_key(self, id: str) -> str:
        pass

    @abstractmethod
    def store_api_key(self, id: str, api_key: str) -> None:
        pass

    @abstractmethod
    def get_api_secret_key(self, id: str) -> str:
        pass

    @abstractmethod
    def store_api_secret_key(self, id: str, api_secret_key: str) -> None:
        pass

    def get_credentials(self, id: str) -> Credentials:
        return Credentials(
            api_key=self.get_api_key(id),
            api_secret_key=self.get_api_secret_key(id)
        )


class LocalCredentialRepository(CredentialsRepository):
    def get_api_key(self, id: str) -> str:
        return os.environ.get(f"{id}_api_key")

    def store_api_key(self, id: str, api_key: str) -> None:
        pass

    def get_api_secret_key(self, id: str) -> str:
        return os.environ.get(f"{id}_api_secret_key")

    def store_api_secret_key(self, id: str, api_secret_key: str) -> None:
        pass


class Bot:
    def __init__(
        self,
        strategy_repository: StrategyRepository,
        credential_repository: CredentialsRepository,
    ) -> None:
        self.strategy_repository = strategy_repository
        self.credential_repository = credential_repository

    def set_executor(self, strategy: Strategy):
        api_key = self.credential_repository.get_api_key(id)
        api_secret_key = self.credential_repository.get_api_secret_key(id)

        if strategy.exchange == "bitvavo":
            strategy.executor = BitvavoExchangeAssetClient(
                strategy.state,
                api_key,
                api_secret_key,
                1,
                get_logger()
            )

    def run(self, id: str) -> None:
        strategy = self.strategy_repository.read(id)
        self.set_executor(strategy)

        data_pipeline = strategy.get_data_pipeline()
        data = data_pipeline.run()
        strategy.run(data)

        self.strategy_repository.store(strategy)
