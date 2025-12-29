from abc import ABC, abstractmethod

from buz.event.event import Event


class PartitionKeySerializer(ABC):
    @abstractmethod
    def generate_key(self, event: Event) -> str:
        pass
