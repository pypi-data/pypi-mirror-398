from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from buz.event.event import Event
from buz.event.meta_subscriber import MetaSubscriber

TEvent = TypeVar("TEvent", bound=Event)


class AsyncSubscriber(Generic[TEvent], MetaSubscriber[TEvent], ABC):
    @abstractmethod
    async def consume(self, event: TEvent) -> None:
        pass
