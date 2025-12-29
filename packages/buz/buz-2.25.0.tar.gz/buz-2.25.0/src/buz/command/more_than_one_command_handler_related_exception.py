from typing import Collection, Union

from buz.command.command import Command
from buz.command.synchronous import CommandHandler
from buz.command.asynchronous import CommandHandler as AsyncCommandHandler


class MoreThanOneCommandHandlerRelatedException(Exception):
    def __init__(self, command: Command, command_handlers: Collection[Union[CommandHandler, AsyncCommandHandler]]):
        self.command = command
        self.command_handlers = command_handlers
        super().__init__(f"There is more than one handler registered for {command.fqn()}.")
