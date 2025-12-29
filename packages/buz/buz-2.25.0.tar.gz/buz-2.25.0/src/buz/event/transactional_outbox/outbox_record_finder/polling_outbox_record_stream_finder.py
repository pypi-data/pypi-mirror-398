from time import sleep
from typing import Generator

from buz.event.transactional_outbox import OutboxCriteriaFactory
from buz.event.transactional_outbox.outbox_record import OutboxRecord
from buz.event.transactional_outbox.outbox_repository import OutboxRepository
from buz.event.transactional_outbox.outbox_record_finder import OutboxRecordStreamFinder


class PollingOutboxRecordStreamFinder(OutboxRecordStreamFinder):
    def __init__(
        self,
        outbox_repository: OutboxRepository,
        criteria_factory: OutboxCriteriaFactory,
        find_iteration_sleep_seconds: int = 2,
    ):
        self.__outbox_repository = outbox_repository
        self.__criteria_factory = criteria_factory
        self.__find_iteration_sleep_seconds = find_iteration_sleep_seconds

    def find(self) -> Generator[OutboxRecord, None, None]:
        while True:
            criteria = self.__criteria_factory.create()
            for record in self.__outbox_repository.find(criteria=criteria):
                yield record

            sleep(self.__find_iteration_sleep_seconds)
