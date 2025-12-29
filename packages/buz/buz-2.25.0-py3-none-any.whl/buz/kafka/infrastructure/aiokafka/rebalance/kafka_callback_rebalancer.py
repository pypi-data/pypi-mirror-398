from datetime import datetime
from logging import Logger
from typing import Awaitable, Callable, Optional

from aiokafka import ConsumerRebalanceListener, TopicPartition


# @see = https://aiokafka.readthedocs.io/en/stable/api.html#aiokafka.abc.ConsumerRebalanceListener.on_partitions_assigned
class KafkaCallbackRebalancer(ConsumerRebalanceListener):
    def __init__(
        self,
        logger: Logger,
        on_partitions_revoked: Callable[[set[TopicPartition]], Awaitable[None]],
        on_partitions_assigned: Callable[[set[TopicPartition]], Awaitable[None]],
    ):
        self.__logger = logger
        self.__on_partition_revoked = on_partitions_revoked
        self.__on_partition_assigned = on_partitions_assigned
        self.__assigned_partitions: set[TopicPartition] = set()
        self.__rebalancing_start_time: Optional[datetime] = None

    async def on_partitions_revoked(self, revoked: set[TopicPartition]) -> None:
        self.__rebalancing_start_time = datetime.now()

        if len(revoked) == 0:
            return None

        self.__logger.info(f"Partitions revoked by the rebalancing process: '{revoked}'")

        await self.__on_partition_revoked(revoked)
        self.__assigned_partitions.difference_update(revoked)

        self.__logger.info(f"Partitions after revoking process: '{self.__assigned_partitions}'")

    async def on_partitions_assigned(self, assigned: set[TopicPartition]) -> None:
        new_partitions_assigned = assigned.difference(self.__assigned_partitions)

        if len(new_partitions_assigned) == 0:
            return None

        self.__logger.info(f"Partitions assigned by the rebalancing process: '{new_partitions_assigned}'")

        await self.__on_partition_assigned(new_partitions_assigned)
        self.__assigned_partitions.update(new_partitions_assigned)

        self.__logger.info(f"Partitions after assigning process: '{self.__assigned_partitions}'")

        if self.__rebalancing_start_time is not None:
            elapsed_time_ms = int((datetime.now() - self.__rebalancing_start_time).total_seconds() * 1000)
            self.__logger.info(
                f"Rebalancing for topic {set(v.topic for v in assigned)} ended, elapsed time: {elapsed_time_ms} ms"
            )
