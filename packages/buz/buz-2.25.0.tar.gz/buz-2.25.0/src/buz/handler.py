from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar

from buz import Message


TMessage = TypeVar("TMessage", bound=Message)


class Handler(Generic[TMessage], ABC):
    @classmethod
    @abstractmethod
    def handles(cls) -> Type[TMessage]:
        pass

    @classmethod
    @abstractmethod
    def fqn(cls) -> str:
        pass
