from abc import ABC, abstractmethod
from typing import Iterable

from buz.event.transactional_outbox import OutboxRecord


class OutboxRecordStreamFinder(ABC):
    @abstractmethod
    def find(self) -> Iterable[OutboxRecord]:
        pass
