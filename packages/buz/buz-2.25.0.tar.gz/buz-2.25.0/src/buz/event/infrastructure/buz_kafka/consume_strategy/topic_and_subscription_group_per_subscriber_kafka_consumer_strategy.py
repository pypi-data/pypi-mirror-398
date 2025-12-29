from typing import Optional
from buz.event.infrastructure.buz_kafka.consume_strategy.consume_strategy import KafkaConsumeStrategy
from buz.event.meta_subscriber import MetaSubscriber


class TopicAndSubscriptionGroupPerSubscriberKafkaConsumerStrategy(KafkaConsumeStrategy):
    def __init__(self, prefix: Optional[str]):
        self._prefix = f"{prefix}." or ""

    def get_topics(self, subscriber: MetaSubscriber) -> list[str]:
        event_class = subscriber.handles()
        return [f"{self._prefix}{event_class.fqn()}"]

    def get_subscription_group(self, subscriber: MetaSubscriber) -> str:
        return subscriber.fqn()
