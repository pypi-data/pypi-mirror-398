from abc import ABC, abstractmethod

from buz.event.transactional_outbox import OutboxRecord


class OutboxRecordValidator(ABC):
    @abstractmethod
    def set_next_validator(self, validator: "OutboxRecordValidator") -> None:
        pass

    @abstractmethod
    def validate(self, record: OutboxRecord) -> None:
        pass
