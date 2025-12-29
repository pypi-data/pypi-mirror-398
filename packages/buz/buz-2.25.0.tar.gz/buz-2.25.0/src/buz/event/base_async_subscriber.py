from abc import ABC
from typing import Generic, TypeVar

from buz.event.event import Event
from buz.event.async_subscriber import AsyncSubscriber
from buz.event.meta_base_subscriber import MetaBaseSubscriber

TEvent = TypeVar("TEvent", bound=Event)


class BaseAsyncSubscriber(Generic[TEvent], AsyncSubscriber[TEvent], MetaBaseSubscriber[TEvent], ABC):
    pass
