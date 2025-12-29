from abc import abstractmethod, ABC

from kombu import Queue


class ConsumeStrategy(ABC):
    @abstractmethod
    def get_queue(self, subscriber_fqn: str) -> Queue:
        pass
