from abc import abstractmethod, ABC
from buz.event import Event


class KafkaPublishStrategy(ABC):
    @abstractmethod
    def get_topic(self, event: Event) -> str:
        pass
