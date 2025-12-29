from abc import abstractmethod, ABC
from buz.event.meta_subscriber import MetaSubscriber


class KafkaConsumeStrategy(ABC):
    @abstractmethod
    def get_topics(self, subscriber: MetaSubscriber) -> list[str]:
        pass

    @abstractmethod
    def get_subscription_group(self, subscriber: MetaSubscriber) -> str:
        pass
