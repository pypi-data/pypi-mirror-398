from typing import Type, Collection, Optional
from buz.event.event import Event
from buz.locator import MessageFqnNotFoundException

EventFqn = str


class FqnToEventMapper:
    def __init__(self, events: Collection[Type[Event]]):
        self.__events = events
        self.__events_map: Optional[dict[EventFqn, Type[Event]]] = None

    def get_message_klass_by_fqn(self, fqn: EventFqn) -> Type[Event]:
        self.__check_events_map_resolved()

        try:
            return self.__events_map[fqn]  # type: ignore[index]
        except KeyError:
            raise MessageFqnNotFoundException(fqn)

    def __check_events_map_resolved(self) -> None:
        if self.__events_map is None:
            self.__events_map = {event.fqn(): event for event in self.__events}
