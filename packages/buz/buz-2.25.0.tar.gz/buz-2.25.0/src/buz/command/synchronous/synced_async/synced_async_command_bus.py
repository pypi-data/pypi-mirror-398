from buz.command.synchronous import CommandBus
from buz.command import Command
from buz.command.asynchronous import CommandBus as AsynchronousCommandbus

from buz.wrapper import AsyncToSync


class SyncedAsyncCommandBus(CommandBus):
    def __init__(self, async_bus: AsynchronousCommandbus):
        self.__wrapped_handler = AsyncToSync[Command, None](async_bus.handle)

    def handle(self, command: Command) -> None:
        self.__wrapped_handler(command)
