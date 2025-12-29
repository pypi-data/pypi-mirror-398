from abc import abstractmethod

from buz.command import Command
from buz.command.synchronous import CommandHandler
from buz.command.synchronous.middleware.handle_middleware import HandleMiddleware, HandleCallable


class BaseHandleMiddleware(HandleMiddleware):
    def on_handle(self, command: Command, command_handler: CommandHandler, handle: HandleCallable) -> None:
        self._before_on_handle(command, command_handler)
        handle(command, command_handler)
        self._after_on_handle(command, command_handler)

    @abstractmethod
    def _before_on_handle(self, command: Command, command_handler: CommandHandler) -> None:
        pass

    @abstractmethod
    def _after_on_handle(self, command: Command, command_handler: CommandHandler) -> None:
        pass
