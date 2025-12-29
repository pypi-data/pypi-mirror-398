from abc import ABC, abstractmethod

from buz.command import Command


class CommandBus(ABC):
    @abstractmethod
    async def handle(self, command: Command) -> None:
        pass
