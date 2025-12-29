from abc import abstractmethod, ABC
from typing import Optional

from kombu import Exchange


class PublishStrategy(ABC):
    @abstractmethod
    def get_exchange(self, event_fqn: str) -> Exchange:
        pass

    @abstractmethod
    def get_routing_key(self, event_fqn: str) -> Optional[str]:
        pass
