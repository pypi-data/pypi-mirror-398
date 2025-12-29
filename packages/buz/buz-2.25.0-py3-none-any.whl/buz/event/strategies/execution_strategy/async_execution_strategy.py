from abc import ABC, abstractmethod


class AsyncExecutionStrategy(ABC):
    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    def request_stop(self) -> None:
        pass
