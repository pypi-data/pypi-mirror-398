from abc import ABC, abstractmethod
from typing import Sequence, Iterable

from buz.event.transactional_outbox import OutboxRecord
from buz.event.transactional_outbox import OutboxCriteria


class OutboxRepository(ABC):
    @abstractmethod
    def save(self, outbox_record: OutboxRecord) -> None:
        pass

    @abstractmethod
    def bulk_create(self, outbox_records: Iterable[OutboxRecord]) -> None:
        pass

    @abstractmethod
    def find(self, criteria: OutboxCriteria) -> Sequence[OutboxRecord]:
        pass

    @abstractmethod
    def bulk_delete(self, outbox_record_ids: Sequence[str]) -> None:
        pass
