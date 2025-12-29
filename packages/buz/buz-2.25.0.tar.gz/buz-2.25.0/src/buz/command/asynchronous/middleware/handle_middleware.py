from abc import abstractmethod
from typing import Callable, Awaitable

from buz.command import Command
from buz.command.asynchronous import CommandHandler
from buz.middleware import Middleware

HandleCallable = Callable[[Command, CommandHandler], Awaitable[None]]


class HandleMiddleware(Middleware):
    @abstractmethod
    async def on_handle(self, command: Command, command_handler: CommandHandler, handle: HandleCallable) -> None:
        pass
