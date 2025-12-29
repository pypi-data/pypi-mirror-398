import time
from asyncio import get_running_loop
from logging import Logger
from typing import Optional, Sequence, cast

from buz.event.infrastructure.models.process_context import ProcessContext

from buz.event import Event
from buz.event.infrastructure.buz_kafka.consume_strategy.kafka_on_fail_strategy import KafkaOnFailStrategy
from buz.event.infrastructure.buz_kafka.exceptions.max_consumer_retry_exception import MaxConsumerRetryException
from buz.event.infrastructure.buz_kafka.exceptions.retry_exception import ConsumerRetryException
from buz.event.infrastructure.buz_kafka.kafka_event_subscriber_executor import KafkaEventSubscriberExecutor
from buz.event.infrastructure.buz_kafka.models.kafka_delivery_context import KafkaDeliveryContext
from buz.event.infrastructure.buz_kafka.models.cdc_process_context import CDCProcessContext
from buz.event.infrastructure.models.execution_context import ExecutionContext
from buz.event.middleware.consume_middleware import ConsumeMiddleware
from buz.event.middleware.consume_middleware_chain_resolver import ConsumeMiddlewareChainResolver
from buz.event.strategies.retry.consume_retrier import ConsumeRetrier
from buz.event.strategies.retry.reject_callback import RejectCallback
from buz.event.subscriber import Subscriber
from buz.kafka.domain.exceptions.not_valid_kafka_message_exception import NotValidKafkaMessageException
from buz.kafka.domain.models.kafka_consumer_record import KafkaConsumerRecord
from buz.kafka.domain.models.kafka_poll_record import KafkaPollRecord
from buz.kafka.infrastructure.deserializers.byte_deserializer import ByteDeserializer
from buz.kafka.infrastructure.deserializers.implementations.cdc.cannot_decode_cdc_message_exception import (
    CannotDecodeCDCMessageException,
)
from buz.kafka.infrastructure.deserializers.implementations.cdc.cdc_record_bytes_to_cdc_payload_deserializer import (
    CDCRecordBytesToCDCPayloadDeserializer,
)
from buz.kafka.infrastructure.serializers.kafka_header_serializer import KafkaHeaderSerializer


class KafkaEventSyncSubscriberExecutor(KafkaEventSubscriberExecutor):
    def __init__(
        self,
        *,
        subscriber: Subscriber,
        logger: Logger,
        consume_middlewares: Optional[Sequence[ConsumeMiddleware]] = None,
        milliseconds_between_retries: int = 5000,
        byte_deserializer: ByteDeserializer[Event],
        header_deserializer: KafkaHeaderSerializer,
        on_fail_strategy: KafkaOnFailStrategy,
        consume_retrier: Optional[ConsumeRetrier] = None,
        reject_callback: Optional[RejectCallback] = None,
        cdc_payload_deserializer: Optional[CDCRecordBytesToCDCPayloadDeserializer] = None,
    ):
        self.__subscriber = subscriber
        self.__logger = logger
        self.__consume_middleware_chain_resolver = ConsumeMiddlewareChainResolver(consume_middlewares or [])
        self.__milliseconds_between_retries = milliseconds_between_retries
        self.__seconds_between_retries = milliseconds_between_retries / 1000.0
        self.__on_fail_strategy = on_fail_strategy
        self.__consume_retrier = consume_retrier
        self.__reject_callback = reject_callback
        self.__byte_deserializer = byte_deserializer
        self.__header_deserializer = header_deserializer
        self.__cdc_payload_deserializer = cdc_payload_deserializer

    async def consume(
        self,
        *,
        kafka_poll_record: KafkaPollRecord,
    ) -> None:
        try:
            if kafka_poll_record.value is None:
                raise NotValidKafkaMessageException("Message is None")

            kafka_record_value = cast(bytes, kafka_poll_record.value)

            deserialized_value = self.__byte_deserializer.deserialize(kafka_record_value)
            process_context = ProcessContext()
            if self.__cdc_payload_deserializer is not None:
                try:
                    deserialized_cdc_payload = self.__cdc_payload_deserializer.deserialize(kafka_record_value)
                    process_context = CDCProcessContext(
                        captured_at_ms=deserialized_cdc_payload.captured_at_ms,
                    )
                except CannotDecodeCDCMessageException as e:
                    self.__logger.error(e.message)

            self.__logger.info(
                f"consuming the event '{deserialized_value.id}' by the subscriber '{self.__subscriber.fqn()}', "
                + f"topic: '{kafka_poll_record.topic}', partition: '{kafka_poll_record.partition}', offset: '{kafka_poll_record.offset}'"
            )

            await get_running_loop().run_in_executor(
                None,
                lambda: self.__execution_callback(
                    subscriber=self.__subscriber,
                    message=KafkaConsumerRecord(
                        value=deserialized_value,
                        headers=self.__header_deserializer.deserialize(kafka_poll_record.headers),
                    ),
                    execution_context=ExecutionContext(
                        delivery_context=KafkaDeliveryContext(
                            topic=kafka_poll_record.topic,
                            consumer_group=self.__subscriber.fqn(),
                            partition=kafka_poll_record.partition,
                            timestamp=kafka_poll_record.timestamp,
                        ),
                        process_context=process_context,
                    ),
                ),
            )

        except NotValidKafkaMessageException:
            self.__logger.error(
                f'The message "{str(kafka_poll_record.value)}" is not valid, it will be consumed but not processed'
            )

    def __execution_callback(
        self, subscriber: Subscriber, message: KafkaConsumerRecord[Event], execution_context: ExecutionContext
    ) -> None:
        self.__consume_middleware_chain_resolver.resolve(
            event=message.value,
            subscriber=subscriber,
            execution_context=execution_context,
            consume=self.__perform_consume,
        )

    def __perform_consume(self, event: Event, subscriber: Subscriber, execution_context: ExecutionContext) -> None:
        number_of_executions = 0
        should_retry = True

        if self.__consume_retrier is not None:
            should_retry = self.__consume_retrier.should_retry(event, [subscriber])

        if should_retry is False:
            max_retry_exception = MaxConsumerRetryException(
                event_id=event.id,
                subscriber_fqn=subscriber.fqn(),
            )

            if self.__on_fail_strategy == KafkaOnFailStrategy.STOP_ON_FAIL:
                raise max_retry_exception

            self.__logger.warning(
                f"The event {event.id} with the subscriber {subscriber.fqn()} has reach the max number of retries, it will be consumed but not processed"
            )

            if self.__reject_callback is not None:
                self.__reject_callback.on_reject(event=event, subscribers=[subscriber], exception=max_retry_exception)

            return

        while should_retry is True:
            try:
                self.__register_retry(event, subscriber)
                number_of_executions += 1
                subscriber.consume(event)
                self.__clean_retries(event, subscriber)
                return
            except Exception as exception:
                if self.__should_retry(event, subscriber) is True:
                    self.__logger.warning(
                        ConsumerRetryException(
                            number_of_executions=number_of_executions,
                            event_id=event.id,
                            subscriber_fqn=subscriber.fqn(),
                        ),
                        exc_info=exception,
                    )
                    time.sleep(self.__seconds_between_retries)
                    continue

                self.__logger.exception(exception)

                if self.__reject_callback is not None:
                    self.__reject_callback.on_reject(event=event, subscribers=[subscriber], exception=exception)

                if self.__on_fail_strategy == KafkaOnFailStrategy.STOP_ON_FAIL:
                    raise exception

                return

    def __should_retry(self, event: Event, subscriber: Subscriber) -> bool:
        if self.__consume_retrier is None:
            return False

        return self.__consume_retrier.should_retry(event, [subscriber])

    def __register_retry(self, event: Event, subscriber: Subscriber) -> None:
        if self.__consume_retrier is None:
            return None

        return self.__consume_retrier.register_retry(event, [subscriber])

    def __clean_retries(self, event: Event, subscriber: Subscriber) -> None:
        if self.__consume_retrier is None:
            return None

        return self.__consume_retrier.clean_retries(event, [subscriber])
