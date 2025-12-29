from typing import Optional

from buz.event.transactional_outbox import OutboxRecord
from buz.event.transactional_outbox.outbox_record_validation.outbox_record_validator import OutboxRecordValidator


class AbstractOutboxRecordValidator(OutboxRecordValidator):
    _next_validator: Optional[OutboxRecordValidator] = None

    def set_next_validator(self, validator: OutboxRecordValidator) -> None:
        self._next_validator = validator

    def validate(self, record: OutboxRecord) -> None:
        if self._next_validator is not None:
            self._next_validator.validate(record)

        return None
