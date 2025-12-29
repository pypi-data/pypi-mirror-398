from typing import Optional

from buz.command import Command
from buz.command.asynchronous import CommandBus
from buz.command.asynchronous import CommandHandler
from buz.command.asynchronous.middleware import HandleMiddleware, HandleMiddlewareChainResolver
from buz.command import MoreThanOneCommandHandlerRelatedException

from buz.locator import Locator


class SelfProcessCommandBus(CommandBus):
    def __init__(
        self,
        locator: Locator[Command, CommandHandler],
        middlewares: Optional[list[HandleMiddleware]] = None,
    ):
        self.__locator = locator
        self.__handle_middleware_chain_resolver = HandleMiddlewareChainResolver(middlewares or [])

    async def handle(self, command: Command) -> None:
        command_handlers = self.__locator.get(command)

        if len(command_handlers) > 1:
            raise MoreThanOneCommandHandlerRelatedException(command, command_handlers)

        command_handler = command_handlers[0]
        await self.__handle_middleware_chain_resolver.resolve(command, command_handler, self.__perform_handle)

    @staticmethod
    async def __perform_handle(command: Command, command_handler: CommandHandler) -> None:
        await command_handler.handle(command)
