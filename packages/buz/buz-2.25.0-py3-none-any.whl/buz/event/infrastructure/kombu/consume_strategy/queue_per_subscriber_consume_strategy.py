from kombu import Queue

from buz.event.infrastructure.kombu.consume_strategy.consume_strategy import ConsumeStrategy
from buz.event.infrastructure.kombu.publish_strategy import PublishStrategy
from buz.locator import Locator


class QueuePerSubscriberConsumeStrategy(ConsumeStrategy):
    def __init__(self, publish_strategy: PublishStrategy, locator: Locator):
        self.__publish_strategy = publish_strategy
        self.__locator = locator

    def get_queue(self, subscriber_fqn: str) -> Queue:
        event_fqn = self.__locator.get_handler_by_fqn(subscriber_fqn).handles().fqn()
        exchange = self.__publish_strategy.get_exchange(event_fqn)
        key = self.__publish_strategy.get_routing_key(event_fqn)
        return Queue(subscriber_fqn, exchange=exchange, key=key)
