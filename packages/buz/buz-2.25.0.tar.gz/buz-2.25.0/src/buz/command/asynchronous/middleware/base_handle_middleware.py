from abc import abstractmethod

from buz.command import Command
from buz.command.asynchronous import CommandHandler
from buz.command.asynchronous.middleware.handle_middleware import HandleMiddleware, HandleCallable


class BaseHandleMiddleware(HandleMiddleware):
    async def on_handle(self, command: Command, command_handler: CommandHandler, handle: HandleCallable) -> None:
        self._before_on_handle(command, command_handler)
        await handle(command, command_handler)
        self._after_on_handle(command, command_handler)

    @abstractmethod
    def _before_on_handle(self, command: Command, command_handler: CommandHandler) -> None:
        pass

    @abstractmethod
    def _after_on_handle(self, command: Command, command_handler: CommandHandler) -> None:
        pass
