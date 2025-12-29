from abc import abstractmethod
from typing import Callable

from buz.command import Command
from buz.command.synchronous import CommandHandler
from buz.middleware import Middleware

HandleCallable = Callable[[Command, CommandHandler], None]


class HandleMiddleware(Middleware):
    @abstractmethod
    def on_handle(self, command: Command, command_handler: CommandHandler, handle: HandleCallable) -> None:
        pass
