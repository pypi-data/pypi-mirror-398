from abc import abstractmethod

from buz.event import Event
from buz.event.middleware import PublishCallable, PublishMiddleware


class BasePublishMiddleware(PublishMiddleware):
    def on_publish(self, event: Event, publish: PublishCallable) -> None:
        self._before_on_publish(event)
        publish(event)
        self._after_on_publish(event)

    @abstractmethod
    def _before_on_publish(self, event: Event) -> None:
        pass

    @abstractmethod
    def _after_on_publish(self, event: Event) -> None:
        pass
