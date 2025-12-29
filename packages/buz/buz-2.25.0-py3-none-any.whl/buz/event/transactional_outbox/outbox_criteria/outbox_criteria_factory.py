from abc import ABC, abstractmethod

from buz.event.transactional_outbox.outbox_criteria import OutboxCriteria


class OutboxCriteriaFactory(ABC):
    @abstractmethod
    def create(self) -> OutboxCriteria:
        pass
