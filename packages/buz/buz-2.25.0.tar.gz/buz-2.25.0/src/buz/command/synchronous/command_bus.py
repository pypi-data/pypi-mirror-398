from abc import ABC, abstractmethod

from buz.command import Command


class CommandBus(ABC):
    @abstractmethod
    def handle(self, command: Command) -> None:
        pass
