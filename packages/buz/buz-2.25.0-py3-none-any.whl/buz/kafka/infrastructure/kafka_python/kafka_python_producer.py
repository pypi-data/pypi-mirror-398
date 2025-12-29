from __future__ import annotations

from typing import Generic, TypeVar, cast

from kafka import KafkaProducer as KafkaPythonLibraryProducer
from kafka.producer.future import FutureRecordMetadata

from buz.kafka.domain.models.kafka_connection_config import KafkaConnectionConfig
from buz.kafka.domain.models.kafka_supported_compression_type import KafkaSupportedCompressionType
from buz.kafka.domain.services.kafka_producer import KafkaProducer
from buz.kafka.infrastructure.serializers.byte_serializer import ByteSerializer
from buz.kafka.infrastructure.serializers.kafka_header_serializer import KafkaHeaderSerializer

T = TypeVar("T")


class KafkaPythonProducer(KafkaProducer, Generic[T]):
    __kafka_producer: KafkaPythonLibraryProducer | None = None
    __SEND_TIMEOUT_SECONDS = 5

    def __init__(
        self,
        *,
        connection_config: KafkaConnectionConfig,
        byte_serializer: ByteSerializer[T],
        retries: int = 0,
        retry_backoff_ms: int = 100,
        compression_type: KafkaSupportedCompressionType | None = None,
    ) -> None:
        self.__connection_config = connection_config
        self.__byte_serializer = byte_serializer
        self.__header_serializer = KafkaHeaderSerializer()
        self.__retries = retries
        self.__retry_backoff_ms = retry_backoff_ms
        self.__compression_type = compression_type

    def _get_kafka_producer(self) -> KafkaPythonLibraryProducer:
        if self.__kafka_producer is None:
            sasl_mechanism = (
                self.__connection_config.credentials.sasl_mechanism.value
                if self.__connection_config.credentials.sasl_mechanism
                else None
            )
            compression_type = self.__compression_type.value if self.__compression_type else None

            self.__kafka_producer = KafkaPythonLibraryProducer(
                client_id=self.__connection_config.client_id,
                bootstrap_servers=self.__connection_config.bootstrap_servers,
                security_protocol=self.__connection_config.credentials.security_protocol.value,
                sasl_mechanism=sasl_mechanism,
                sasl_plain_username=self.__connection_config.credentials.user,
                sasl_plain_password=self.__connection_config.credentials.password,
                retries=self.__retries,
                retry_backoff_ms=self.__retry_backoff_ms,
                compression_type=compression_type,
            )

        return self.__kafka_producer

    def connect(self):
        self._get_kafka_producer()

    def disconnect(self) -> None:
        if self.__kafka_producer is not None:
            self.__kafka_producer.close()
            self.__kafka_producer = None

    def produce(
        self,
        *,
        topic: str,
        message: T,
        partition_key: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        serialized_headers = self.__header_serializer.serialize(headers) if headers is not None else None
        kafka_producer = self._get_kafka_producer()

        message_future = cast(
            FutureRecordMetadata,
            kafka_producer.send(
                topic=topic,
                value=self.__byte_serializer.serialize(message),
                headers=serialized_headers,
                key=partition_key.encode("utf-8") if partition_key is not None else None,
            ),
        )

        # We are forcing a flush because the task related with the send is asynchronous, and we want that the event to be sent after call produce
        message_future.get(self.__SEND_TIMEOUT_SECONDS)
