from abc import ABC
from typing import Generic, Type, TypeVar, cast, get_type_hints

from buz.event.event import Event
from buz.event.meta_subscriber import MetaSubscriber

TEvent = TypeVar("TEvent", bound=Event)


class MetaBaseSubscriber(Generic[TEvent], MetaSubscriber[TEvent], ABC):
    @classmethod
    def fqn(cls) -> str:
        return f"subscriber.{cls.__module__}.{cls.__name__}"

    @classmethod
    def handles(cls) -> Type[TEvent]:
        consume_types = get_type_hints(cls.consume)

        t_event = consume_types.get("event")
        if t_event is None:
            raise TypeError("event parameter not found in consume method")

        if not issubclass(t_event, Event):
            raise TypeError("event parameter is not an buz.event.Event subclass")

        return cast(Type[TEvent], t_event)
