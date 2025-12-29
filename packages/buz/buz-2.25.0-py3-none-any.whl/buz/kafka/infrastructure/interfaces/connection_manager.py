from abc import ABC, abstractmethod


class ConnectionManager(ABC):
    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass
