from __future__ import annotations


class NotAllPartitionAssignedException(Exception):
    def __init__(
        self,
        *,
        topic_name: str,
        consumer_group: str,
    ) -> None:
        super().__init__(
            f'Not all the partitions in the consumer group "{consumer_group}" were assigned in the topic "{topic_name}". Please disconnect the rest of subscribers'
        )
