from abc import ABC, abstractmethod
from typing import Awaitable, Generic, Type, TypeVar, Union

from buz import Handler
from buz.event.event import Event

TEvent = TypeVar("TEvent", bound=Event)


class MetaSubscriber(Generic[TEvent], Handler[TEvent], ABC):
    @abstractmethod
    def consume(self, event: TEvent) -> Union[None, Awaitable[None]]:
        pass

    @classmethod
    @abstractmethod
    def handles(cls) -> Type[TEvent]:
        pass
