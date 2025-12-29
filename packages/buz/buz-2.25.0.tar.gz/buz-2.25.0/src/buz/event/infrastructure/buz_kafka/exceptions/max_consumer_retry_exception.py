class MaxConsumerRetryException(Exception):
    def __init__(
        self,
        *,
        event_id: str,
        subscriber_fqn: str,
    ) -> None:
        super().__init__(f"Max retries reached, discarding event {event_id} for subscriber {subscriber_fqn}")
