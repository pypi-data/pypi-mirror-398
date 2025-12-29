from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Generic, Optional, TypeVar

from buz.kafka.infrastructure.interfaces.async_connection_manager import AsyncConnectionManager

T = TypeVar("T")


class AsyncKafkaProducer(AsyncConnectionManager, ABC, Generic[T]):
    @abstractmethod
    async def produce(
        self,
        *,
        topic: str,
        message: T,
        partition_key: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        pass
