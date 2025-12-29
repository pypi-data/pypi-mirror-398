from typing import Optional
from buz.event import Event
from buz.event.infrastructure.buz_kafka.publish_strategy.publish_strategy import KafkaPublishStrategy


class TopicPerEventKafkaPublishStrategy(KafkaPublishStrategy):
    def __init__(self, prefix: Optional[str]):
        self._prefix = f"{prefix}." or ""

    def get_topic(self, event: Event) -> str:
        return f"{self._prefix}{event.fqn()}"
