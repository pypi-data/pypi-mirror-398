import dataclasses
from uuid import UUID

from buz.event import Event
from buz.event.transactional_outbox.outbox_record import OutboxRecord


class EventToOutboxRecordTranslator:
    def translate(self, event: Event) -> OutboxRecord:
        payload = dataclasses.asdict(event)
        payload.pop("id")
        payload.pop("created_at")
        payload.pop("metadata")
        partition_key = event.partition_key()
        return OutboxRecord(
            event_id=UUID(event.id),
            event_fqn=event.fqn(),
            created_at=event.parsed_created_at(),
            event_payload=payload,
            event_metadata=dict(event.metadata),
            partition_key=partition_key,
        )
