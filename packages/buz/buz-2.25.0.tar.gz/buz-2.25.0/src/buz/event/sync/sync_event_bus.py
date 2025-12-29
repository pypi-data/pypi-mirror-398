from typing import Optional, Iterable

from buz.event.infrastructure.models.process_context import ProcessContext

from buz.event import Event, EventBus, Subscriber
from buz.event.infrastructure.models.execution_context import ExecutionContext
from buz.event.middleware import (
    PublishMiddleware,
    ConsumeMiddleware,
    PublishMiddlewareChainResolver,
    ConsumeMiddlewareChainResolver,
)
from buz.event.sync.models.sync_delivery_context import SyncDeliveryContext
from buz.locator import Locator


class SyncEventBus(EventBus):
    def __init__(
        self,
        locator: Locator[Event, Subscriber],
        publish_middlewares: Optional[list[PublishMiddleware]] = None,
        consume_middlewares: Optional[list[ConsumeMiddleware]] = None,
    ):
        self.__locator = locator
        self.__publish_middleware_chain_resolver = PublishMiddlewareChainResolver(publish_middlewares or [])
        self.__consume_middleware_chain_resolver = ConsumeMiddlewareChainResolver(consume_middlewares or [])

    def publish(self, event: Event) -> None:
        self.__publish_middleware_chain_resolver.resolve(event, self.__perform_publish)

    def __perform_publish(self, event: Event) -> None:
        subscribers = self.__locator.get(event)
        execution_context = ExecutionContext(delivery_context=SyncDeliveryContext(), process_context=ProcessContext())
        for subscriber in subscribers:
            self.__consume_middleware_chain_resolver.resolve(
                event=event,
                subscriber=subscriber,
                execution_context=execution_context,
                consume=self.__perform_consume,
            )

    def __perform_consume(self, event: Event, subscriber: Subscriber, execution_context: ExecutionContext) -> None:
        subscriber.consume(event)

    def bulk_publish(self, events: Iterable[Event]) -> None:
        for event in events:
            self.publish(event)
