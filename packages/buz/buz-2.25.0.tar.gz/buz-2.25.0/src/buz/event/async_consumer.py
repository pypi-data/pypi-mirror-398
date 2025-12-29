from abc import ABC, abstractmethod


class AsyncConsumer(ABC):
    @abstractmethod
    async def run(self) -> None:
        pass

    @abstractmethod
    def request_stop(self) -> None:
        pass
