from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar

from buz import Handler
from buz.command.command import Command


TCommand = TypeVar("TCommand", bound=Command)


class CommandHandler(Generic[TCommand], Handler[TCommand], ABC):
    @classmethod
    @abstractmethod
    def handles(cls) -> Type[TCommand]:
        pass

    @abstractmethod
    async def handle(self, command: TCommand) -> None:
        pass
