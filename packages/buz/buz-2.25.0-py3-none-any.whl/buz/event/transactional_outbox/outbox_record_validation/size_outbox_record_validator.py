from typing import Optional

import orjson
from pympler.asizeof import asizeof

from buz.event.transactional_outbox import OutboxRecord
from buz.event.transactional_outbox.outbox_record_validation.abstract_outbox_record_validator import (
    AbstractOutboxRecordValidator,
)
from buz.event.transactional_outbox.outbox_record_validation.outbox_record_size_not_allowed_exception import (
    OutboxRecordSizeNotAllowedException,
)


class SizeOutboxRecordValidator(AbstractOutboxRecordValidator):
    def __init__(self, size_limit_in_bytes: int = 1000000):
        self.__size_limit_in_bytes = size_limit_in_bytes
        super().__init__()

    def validate(self, record: OutboxRecord) -> None:
        try:
            size = asizeof(self.__record_to_json(record))
        except Exception:
            size = self.__fallback_size_validator(record)

        if size >= self.__size_limit_in_bytes:
            raise OutboxRecordSizeNotAllowedException(
                record=record, size_limit_in_bytes=self.__size_limit_in_bytes, record_size=size
            )

        return super().validate(record)

    def __record_to_json(self, record: OutboxRecord) -> bytes:
        [created_at, delivered_at, delivery_paused_at] = self.__get_dates_parsed_for_json(record)
        return orjson.dumps(
            {
                "created_at": created_at,
                "delivered_at": delivered_at,
                "delivery_paused_at": delivery_paused_at,
                "delivery_errors": record.delivery_errors,
                "event_id": record.event_id,
                "event_fqn": record.event_fqn,
                "event_payload": record.event_payload,
            }
        )

    def __get_dates_parsed_for_json(self, record: OutboxRecord) -> tuple[str, Optional[str], Optional[str]]:
        parsed_created_at_json = record.created_at.strftime(record.DATE_TIME_FORMAT)
        parsed_delivered_at_json = (
            record.delivered_at.strftime(record.DATE_TIME_FORMAT) if record.delivered_at is not None else None
        )
        parsed_delivery_paused_at_json = (
            record.delivery_paused_at.strftime(record.DATE_TIME_FORMAT)
            if record.delivery_paused_at is not None
            else None
        )
        return parsed_created_at_json, parsed_delivered_at_json, parsed_delivery_paused_at_json

    def __fallback_size_validator(self, record: OutboxRecord) -> int:
        return asizeof(record)
