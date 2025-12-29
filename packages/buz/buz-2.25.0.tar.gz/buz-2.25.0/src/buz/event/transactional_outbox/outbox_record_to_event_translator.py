from typing import cast

from buz.event import Event
from buz.event.transactional_outbox import FqnToEventMapper
from buz.event.transactional_outbox import OutboxRecord


class OutboxRecordToEventTranslator:
    def __init__(self, fqn_to_event_mapper: FqnToEventMapper):
        self.__fqn_to_event_mapper = fqn_to_event_mapper

    def translate(self, outbox_record: OutboxRecord) -> Event:
        event_klass = self.__fqn_to_event_mapper.get_message_klass_by_fqn(outbox_record.event_fqn)
        return cast(
            Event,
            event_klass.restore(
                id=str(outbox_record.event_id),
                created_at=outbox_record.parsed_created_at(),
                metadata=outbox_record.event_metadata,
                **outbox_record.event_payload,
            ),
        )
