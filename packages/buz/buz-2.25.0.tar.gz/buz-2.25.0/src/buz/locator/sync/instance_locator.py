from collections import defaultdict
from typing import DefaultDict, Generic, TypeVar, Type, cast

from buz import Handler
from buz import Message
from buz.locator import Locator, HandlerFqnNotFoundException, MessageFqnNotFoundException
from buz.locator.sync import HandlerAlreadyRegisteredException
from buz.locator.sync import HandlerNotRegisteredException

K = TypeVar("K", bound=Message)
V = TypeVar("V", bound=Handler)


class InstanceLocator(Locator, Generic[K, V]):
    def __init__(self) -> None:
        self.__mapping: DefaultDict[str, list[V]] = defaultdict(list)

    def register(self, handler: V) -> None:
        message_fqn = handler.handles().fqn()
        self.__guard_handler_already_registered(message_fqn, handler)
        self.__mapping[message_fqn].append(handler)

    def __guard_handler_already_registered(self, message_fqn: str, handler: V) -> None:
        if handler in self.__mapping[message_fqn]:
            raise HandlerAlreadyRegisteredException(handler)

    def unregister(self, handler: V) -> None:
        message_fqn = handler.handles().fqn()
        self.__guard_subscriber_not_registered(message_fqn, handler)
        self.__mapping[message_fqn].remove(handler)

    def __guard_subscriber_not_registered(self, message_fqn: str, handler: V) -> None:
        if handler not in self.__mapping[message_fqn]:
            raise HandlerNotRegisteredException(handler)

    def get(self, message: K) -> list[V]:
        return self.__mapping.get(message.fqn(), [])

    def get_handler_by_fqn(self, handler_fqn: str) -> V:
        for handlers in self.__mapping.values():
            for handler in handlers:
                if handler.fqn() == handler_fqn:
                    return handler
        raise HandlerFqnNotFoundException(handler_fqn)

    def get_message_klass_by_fqn(self, message_fqn: str) -> Type[K]:
        try:
            handler = self.__mapping.get(message_fqn, [])[0]
            return cast(Type[K], handler.handles())
        except (IndexError, TypeError):
            raise MessageFqnNotFoundException(message_fqn)
