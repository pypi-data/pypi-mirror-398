from __future__ import annotations


class ConsumerGroupNotFoundException(Exception):
    def __init__(self, consumer_group: str) -> None:
        super().__init__(f'The consumer group "{consumer_group}" has not been found')
