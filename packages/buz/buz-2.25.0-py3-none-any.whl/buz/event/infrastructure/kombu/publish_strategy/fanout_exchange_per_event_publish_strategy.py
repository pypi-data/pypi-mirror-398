from typing import Optional

from kombu import Exchange

from buz.event.infrastructure.kombu.publish_strategy import PublishStrategy


class FanoutExchangePerEventPublishStrategy(PublishStrategy):
    def get_exchange(self, event_fqn: str) -> Exchange:
        return Exchange(event_fqn, "fanout", durable=True)

    def get_routing_key(self, event_fqn: str) -> Optional[str]:
        return None
