from typing import Optional, Iterable

from buz.event import Event, EventBus
from buz.event.middleware.publish_middleware import PublishMiddleware
from buz.event.middleware.publish_middleware_chain_resolver import PublishMiddlewareChainResolver
from buz.event.transactional_outbox import OutboxRecord
from buz.event.transactional_outbox.event_to_outbox_record_translator import EventToOutboxRecordTranslator
from buz.event.transactional_outbox.outbox_record_validation.outbox_record_validator import OutboxRecordValidator
from buz.event.transactional_outbox.outbox_repository import OutboxRepository


class TransactionalOutboxEventBus(EventBus):
    def __init__(
        self,
        outbox_repository: OutboxRepository,
        event_to_outbox_record_translator: EventToOutboxRecordTranslator,
        outbox_record_validator: Optional[OutboxRecordValidator] = None,
        publish_middlewares: Optional[list[PublishMiddleware]] = None,
    ) -> None:
        self.__outbox_repository = outbox_repository
        self.__event_to_outbox_record_translator = event_to_outbox_record_translator
        self.__outbox_record_validator = outbox_record_validator
        self.__publish_middleware = publish_middlewares
        self.__publish_middleware_chain_resolver = PublishMiddlewareChainResolver(self.__publish_middleware or [])

    def publish(self, event: Event) -> None:
        self.__publish_middleware_chain_resolver.resolve(event, self.__perform_publish)

    def __perform_publish(self, event: Event) -> None:
        outbox_record = self.__process_event(event)
        self.__outbox_repository.save(outbox_record)

    def bulk_publish(self, events: Iterable[Event]) -> None:
        publish_middleware_chain_resolver = PublishMiddlewareChainResolver(self.__publish_middleware or [])
        outbox_records: list[OutboxRecord] = []

        for event in events:
            publish_middleware_chain_resolver.resolve(event, lambda resolved_event: None)
            outbox_records.append(self.__process_event(event))

        if len(outbox_records) == 0:
            return None

        self.__outbox_repository.bulk_create(outbox_records)

    def __process_event(self, event: Event) -> OutboxRecord:
        outbox_record = self.__translate_event(event)
        self.__validate_outbox_record(outbox_record)
        return outbox_record

    def __translate_event(self, event: Event) -> OutboxRecord:
        return self.__event_to_outbox_record_translator.translate(event)

    def __validate_outbox_record(self, outbox_record: OutboxRecord) -> None:
        if self.__outbox_record_validator is not None:
            self.__outbox_record_validator.validate(record=outbox_record)
