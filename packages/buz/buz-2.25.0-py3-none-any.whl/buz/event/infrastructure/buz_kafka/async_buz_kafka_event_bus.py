from logging import Logger
from typing import Collection, Optional

from buz.event import Event
from buz.event.async_event_bus import AsyncEventBus
from buz.event.exceptions.event_not_published_exception import EventNotPublishedException
from buz.event.infrastructure.buz_kafka.exceptions.kafka_event_bus_config_not_valid_exception import (
    KafkaEventBusConfigNotValidException,
)
from buz.event.infrastructure.buz_kafka.publish_strategy.publish_strategy import KafkaPublishStrategy
from buz.event.middleware.async_publish_middleware import AsyncPublishMiddleware
from buz.event.middleware.async_publish_middleware_chain_resolver import AsyncPublishMiddlewareChainResolver
from buz.kafka.domain.exceptions.topic_already_created_exception import KafkaTopicsAlreadyCreatedException
from buz.kafka.domain.models.auto_create_topic_configuration import AutoCreateTopicConfiguration
from buz.kafka.domain.models.create_kafka_topic import CreateKafkaTopic
from buz.kafka.domain.services.async_kafka_producer import AsyncKafkaProducer
from buz.kafka.domain.services.kafka_admin_client import KafkaAdminClient


class AsyncBuzKafkaEventBus(AsyncEventBus):
    def __init__(
        self,
        *,
        publish_strategy: KafkaPublishStrategy,
        producer: AsyncKafkaProducer,
        logger: Logger,
        kafka_admin_client: Optional[KafkaAdminClient] = None,
        publish_middlewares: Optional[list[AsyncPublishMiddleware]] = None,
        auto_create_topic_configuration: Optional[AutoCreateTopicConfiguration] = None,
    ):
        self.__publish_middleware_chain_resolver = AsyncPublishMiddlewareChainResolver(publish_middlewares or [])
        self.__publish_strategy = publish_strategy
        self.__producer = producer
        self.__topics_checked: dict[str, bool] = {}
        self.__kafka_admin_client = kafka_admin_client
        self.__auto_create_topic_configuration = auto_create_topic_configuration
        self.__logger = logger
        self.__check_kafka_admin_client_is_needed()

    def __check_kafka_admin_client_is_needed(self) -> None:
        if self.__kafka_admin_client is None and self.__auto_create_topic_configuration is not None:
            raise KafkaEventBusConfigNotValidException(
                "A KafkaAdminClient is needed to create topics when 'auto_create_topic_configuration' is set."
            )

    async def publish(self, event: Event) -> None:
        await self.__publish_middleware_chain_resolver.resolve(event, self.__perform_publish)

    async def __perform_publish(self, event: Event) -> None:
        try:
            topic = self.__publish_strategy.get_topic(event)

            if self.__auto_create_topic_configuration is not None and self.__is_topic_created(topic) is False:
                try:
                    self.__logger.info(f"Creating missing topic: {topic}..")
                    self.__get_kafka_admin_client().create_topics(
                        topics=[
                            CreateKafkaTopic(
                                name=topic,
                                partitions=self.__auto_create_topic_configuration.partitions,
                                replication_factor=self.__auto_create_topic_configuration.replication_factor,
                                configs=self.__auto_create_topic_configuration.configs,
                            )
                        ]
                    )
                    self.__logger.info(f"Created missing topic: {topic}")
                    self.__topics_checked[topic] = True
                except KafkaTopicsAlreadyCreatedException:
                    pass

            headers = self.__get_event_headers(event)
            await self.__producer.produce(
                message=event,
                headers=headers,
                topic=topic,
                partition_key=event.partition_key(),
            )
        except Exception as exc:
            raise EventNotPublishedException(event) from exc

    def __get_kafka_admin_client(self) -> KafkaAdminClient:
        if self.__kafka_admin_client is None:
            raise KafkaEventBusConfigNotValidException("KafkaAdminClient is not set.")
        return self.__kafka_admin_client

    def __is_topic_created(self, topic: str) -> bool:
        is_topic_created = self.__topics_checked.get(topic, None)

        if is_topic_created is not None:
            return is_topic_created

        is_topic_created = self.__get_kafka_admin_client().is_topic_created(topic)
        self.__topics_checked[topic] = is_topic_created

        return is_topic_created

    async def bulk_publish(self, events: Collection[Event]) -> None:
        for event in events:
            await self.publish(event)

    def __get_event_headers(self, event: Event) -> dict:
        return {"id": event.id}

    async def connect(self) -> None:
        await self.__producer.connect()

    async def disconnect(self) -> None:
        await self.__producer.disconnect()
