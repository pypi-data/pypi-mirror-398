from logging import Logger
from typing import Union

from buz.event import EventBus
from buz.event.transactional_outbox import (
    OutboxRepository,
    OutboxRecordToEventTranslator,
    OutboxRecordStreamFinder,
    OutboxRecord,
)
from buz.locator import MessageFqnNotFoundException
from buz.event.exceptions.event_not_published_exception import EventNotPublishedException


class TransactionalOutboxWorker:
    def __init__(
        self,
        outbox_repository: OutboxRepository,
        outbox_record_stream_finder: OutboxRecordStreamFinder,
        outbox_record_to_event_translator: OutboxRecordToEventTranslator,
        event_bus: EventBus,
        logger: Logger,
        max_retries: int,
    ):
        self.__outbox_repository = outbox_repository
        self.__outbox_record_stream_finder = outbox_record_stream_finder
        self.__outbox_record_to_event_translator = outbox_record_to_event_translator
        self.__event_bus = event_bus
        self.__logger = logger
        self.__max_retries = max_retries

    def start(self) -> None:
        for outbox_record in self.__outbox_record_stream_finder.find():
            try:
                event = self.__outbox_record_to_event_translator.translate(outbox_record)

                self.__event_bus.publish(event)
                outbox_record.mark_as_delivered()

            except (MessageFqnNotFoundException, EventNotPublishedException) as e:
                self.__mark_delivery_error(outbox_record)
                self.__log_first_time_exception(e, outbox_record)

            except Exception as e:
                self.__logger.exception(e)
                self.__mark_delivery_error(outbox_record)

            self.__outbox_repository.save(outbox_record)

    def __mark_delivery_error(self, outbox_record: OutboxRecord) -> None:
        outbox_record.mark_delivery_error()
        if outbox_record.delivery_errors >= self.__max_retries:
            outbox_record.pause_delivery()

    def __log_first_time_exception(
        self, exc: Union[MessageFqnNotFoundException, EventNotPublishedException], outbox_record: OutboxRecord
    ) -> None:
        if outbox_record.delivery_errors == 1:
            self.__logger.exception(exc)
