from abc import abstractmethod
from typing import Callable

from buz.event import Event
from buz.middleware import Middleware

PublishCallable = Callable[[Event], None]


class PublishMiddleware(Middleware):
    @abstractmethod
    def on_publish(self, event: Event, publish: PublishCallable) -> None:
        pass
