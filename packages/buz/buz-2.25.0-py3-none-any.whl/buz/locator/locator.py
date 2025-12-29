from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Sequence, Type

from buz import Handler
from buz import Message

K = TypeVar("K", bound=Message)
V = TypeVar("V", bound=Handler)


class Locator(ABC, Generic[K, V]):
    @abstractmethod
    def get(self, message: K) -> Sequence[V]:
        pass

    @abstractmethod
    def get_handler_by_fqn(self, handler_fqn: str) -> V:
        pass

    @abstractmethod
    def get_message_klass_by_fqn(self, message_fqn: str) -> Type[K]:
        pass
