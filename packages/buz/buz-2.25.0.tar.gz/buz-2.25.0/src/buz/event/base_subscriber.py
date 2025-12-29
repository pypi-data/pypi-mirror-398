from abc import ABC
from typing import Generic, TypeVar

from buz.event.event import Event
from buz.event.subscriber import Subscriber
from buz.event.meta_base_subscriber import MetaBaseSubscriber

TEvent = TypeVar("TEvent", bound=Event)


class BaseSubscriber(Generic[TEvent], Subscriber[TEvent], MetaBaseSubscriber[TEvent], ABC):
    pass
