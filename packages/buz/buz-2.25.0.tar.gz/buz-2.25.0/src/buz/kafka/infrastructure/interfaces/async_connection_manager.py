from abc import ABC, abstractmethod


class AsyncConnectionManager(ABC):
    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass
