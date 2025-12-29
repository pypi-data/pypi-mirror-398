from abc import ABC, abstractmethod
from typing import Sequence

from buz.event.dead_letter_queue.dlq_criteria import DlqCriteria
from buz.event.dead_letter_queue.dlq_record import DlqRecord, DlqRecordId


class DlqRepository(ABC):
    @abstractmethod
    def save(self, dlq_record: DlqRecord) -> None:
        pass

    @abstractmethod
    def find_one_or_fail_by_criteria(self, criteria: DlqCriteria) -> DlqRecord:
        pass

    @abstractmethod
    def delete(self, dlq_record_id: DlqRecordId) -> None:
        pass

    @abstractmethod
    def bulk_delete(self, dlq_record_ids: Sequence[DlqRecordId]) -> None:
        pass
