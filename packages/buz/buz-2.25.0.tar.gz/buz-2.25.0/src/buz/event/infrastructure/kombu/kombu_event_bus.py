from dataclasses import asdict
from typing import Optional, Iterable

from kombu import Connection, Exchange, Producer
from kombu.entity import PERSISTENT_DELIVERY_MODE

from buz.event import Event, EventBus
from buz.event.exceptions.event_not_published_exception import EventNotPublishedException
from buz.event.infrastructure.kombu.allowed_kombu_serializer import AllowedKombuSerializer
from buz.event.infrastructure.kombu.publish_strategy import PublishStrategy
from buz.event.infrastructure.kombu.retry_strategy.publish_retry_policy import PublishRetryPolicy
from buz.event.infrastructure.kombu.retry_strategy.simple_publish_retry_policy import SimplePublishRetryPolicy
from buz.event.middleware import (
    PublishMiddleware,
    PublishMiddlewareChainResolver,
)


class KombuEventBus(EventBus):
    def __init__(
        self,
        connection: Connection,
        publish_strategy: PublishStrategy,
        publish_retry_policy: PublishRetryPolicy = SimplePublishRetryPolicy(),
        serializer: Optional[AllowedKombuSerializer] = AllowedKombuSerializer.JSON,
        publish_middlewares: Optional[list[PublishMiddleware]] = None,
    ):
        self.__connection = connection
        self.__publish_strategy = publish_strategy
        self.__publish_retry_policy = publish_retry_policy
        self.__serializer = serializer
        self.__publish_middleware_chain_resolver = PublishMiddlewareChainResolver(publish_middlewares or [])
        self.__declared_exchanges: set[Exchange] = set()
        self.__producer: Optional[Producer] = None

    def publish(self, event: Event) -> None:
        self.__publish_middleware_chain_resolver.resolve(event, self.__perform_publish)

    def __perform_publish(self, event: Event) -> None:
        try:
            event_fqn = event.fqn()
            exchange = self.__get_exchange(event_fqn)
            routing_key = self.__publish_strategy.get_routing_key(event_fqn)

            producer = self.__get_producer()

            body = self.__get_body(event)
            headers = self.__get_headers(event)

            producer.publish(
                body,
                exchange=exchange,
                routing_key=routing_key,
                retry=True,
                retry_policy=self.__get_publish_retry_policy_for_event(event),
                headers=headers,
                delivery_mode=PERSISTENT_DELIVERY_MODE,
            )
        except Exception as exc:
            raise EventNotPublishedException(event) from exc

    def __get_publish_retry_policy_for_event(self, event: Event) -> dict:
        return {
            "max_retries": self.__publish_retry_policy.max_retries(event),
            "interval_start": self.__publish_retry_policy.interval_start(event),
            "interval_step": self.__publish_retry_policy.interval_step(event),
            "interval_max": self.__publish_retry_policy.interval_max(event),
            "errback": lambda exc, interval_range: self.__publish_retry_policy.error_callback(
                event, exc, interval_range
            ),
        }

    def __get_exchange(self, event_fqn: str) -> Exchange:
        exchange = self.__publish_strategy.get_exchange(event_fqn)

        if exchange not in self.__declared_exchanges:
            self.__declare_exchange(exchange)

        return exchange

    def __declare_exchange(self, exchange: Exchange) -> None:
        auto_retry_declare = self.__connection.autoretry(exchange.declare)
        auto_retry_declare()
        self.__declared_exchanges.add(exchange)

    def __get_producer(self) -> Producer:
        if self.__producer is None:
            self.__producer = self.__connection.Producer(serializer=self.__serializer)

        return self.__producer

    def __get_body(self, event: Event) -> dict:
        return asdict(event)

    def __get_headers(self, event: Event) -> dict:
        return {"fqn": event.fqn()}

    def bulk_publish(self, events: Iterable[Event]) -> None:
        for event in events:
            self.publish(event)
