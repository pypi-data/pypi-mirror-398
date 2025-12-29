from __future__ import annotations

from ssl import SSLContext
from typing import Generic, Optional, TypeVar

from aiokafka import AIOKafkaProducer as NativeAIOKafkaProducer
from aiokafka.helpers import create_ssl_context

from buz.kafka.domain.models.kafka_connection_config import KafkaConnectionConfig
from buz.kafka.domain.models.kafka_supported_compression_type import KafkaSupportedCompressionType
from buz.kafka.domain.models.kafka_supported_security_protocols import KafkaSupportedSecurityProtocols
from buz.kafka.domain.services.async_kafka_producer import AsyncKafkaProducer
from buz.kafka.infrastructure.serializers.byte_serializer import ByteSerializer
from buz.kafka.infrastructure.serializers.kafka_header_serializer import KafkaHeaderSerializer

T = TypeVar("T")


class AIOKafkaProducer(AsyncKafkaProducer, Generic[T]):
    __DEFAULT_REQUEST_TIMEOUT_MS = 5000
    __kafka_producer: Optional[NativeAIOKafkaProducer] = None

    def __init__(
        self,
        *,
        connection_config: KafkaConnectionConfig,
        byte_serializer: ByteSerializer[T],
        compression_type: Optional[KafkaSupportedCompressionType] = None,
        retry_backoff_ms: int = 100,
    ) -> None:
        self.__connection_config = connection_config
        self.__byte_serializer = byte_serializer
        self.__header_serializer = KafkaHeaderSerializer()
        self.__compression_type = compression_type
        self.__retry_backoff_ms = retry_backoff_ms

    async def _get_aiokafka_producer(self) -> NativeAIOKafkaProducer:
        if self.__kafka_producer:
            return self.__kafka_producer

        ssl_context: Optional[SSLContext] = None

        sasl_mechanism = (
            self.__connection_config.credentials.sasl_mechanism.value
            if self.__connection_config.credentials.sasl_mechanism
            else "PLAIN"
        )

        if self.__connection_config.credentials.security_protocol == KafkaSupportedSecurityProtocols.SASL_SSL:
            ssl_context = create_ssl_context()

        self.__kafka_producer = NativeAIOKafkaProducer(
            client_id=self.__connection_config.client_id,
            bootstrap_servers=",".join(self.__connection_config.bootstrap_servers),
            sasl_mechanism=sasl_mechanism,
            ssl_context=ssl_context,
            sasl_plain_username=self.__connection_config.credentials.user,
            sasl_plain_password=self.__connection_config.credentials.password,
            retry_backoff_ms=self.__retry_backoff_ms,
            request_timeout_ms=self.__DEFAULT_REQUEST_TIMEOUT_MS,
            compression_type=self.__compression_type.value if self.__compression_type else None,
        )

        await self.__kafka_producer.start()

        return self.__kafka_producer

    async def connect(self) -> None:
        await self._get_aiokafka_producer()

    async def disconnect(self) -> None:
        if self.__kafka_producer is None:
            return None
        await self.__kafka_producer.stop()
        self.__kafka_producer = None

    async def produce(
        self,
        *,
        topic: str,
        message: T,
        partition_key: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        serialized_headers = self.__header_serializer.serialize(headers) if headers is not None else None
        kafka_producer = await self._get_aiokafka_producer()

        await kafka_producer.send_and_wait(
            topic=topic,
            value=self.__byte_serializer.serialize(message),
            headers=serialized_headers,
            key=partition_key.encode("utf-8") if partition_key else None,
        )

    async def close(self) -> None:
        if self.__kafka_producer is not None:
            await self.__kafka_producer.stop()
            self.__kafka_producer = None
