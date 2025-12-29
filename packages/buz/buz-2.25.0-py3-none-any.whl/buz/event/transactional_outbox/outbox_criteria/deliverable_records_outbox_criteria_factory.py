from buz.event.transactional_outbox.outbox_criteria import OutboxCriteria, OutboxCriteriaFactory, OutboxSortingCriteria


class DeliverableRecordsOutboxCriteriaFactory(OutboxCriteriaFactory):
    def create(self) -> OutboxCriteria:
        return OutboxCriteria(delivered_at=None, order_by=OutboxSortingCriteria.CREATED_AT, delivery_paused=False)
