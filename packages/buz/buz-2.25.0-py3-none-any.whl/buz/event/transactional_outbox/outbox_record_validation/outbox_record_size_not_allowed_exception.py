from buz.event.transactional_outbox import OutboxRecord
from buz.event.transactional_outbox.outbox_record_validation.outbox_record_validation_exception import (
    OutboxRecordValidationException,
)


class OutboxRecordSizeNotAllowedException(OutboxRecordValidationException):
    def __init__(self, record: OutboxRecord, size_limit_in_bytes: int, record_size: int):
        self.record = record
        self.size_limit_in_bytes = size_limit_in_bytes
        self.record_size = record_size
        super().__init__(
            error_message=(
                f"Record with id: {record.event_id} and fqn: {record.event_fqn} has size of "
                f"{record_size} bytes while the limit is {size_limit_in_bytes} bytes"
            )
        )
