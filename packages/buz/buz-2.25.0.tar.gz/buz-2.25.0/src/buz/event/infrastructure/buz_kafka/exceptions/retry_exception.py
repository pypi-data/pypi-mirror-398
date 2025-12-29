class ConsumerRetryException(Exception):
    def __init__(
        self,
        *,
        event_id: str,
        subscriber_fqn: str,
        number_of_executions: int,
    ) -> None:
        super().__init__(
            f"An exception happened during the consumption of the event '{event_id}' by the subscriber '{subscriber_fqn}' "
            + f"during execution number '{number_of_executions}'. Retrying the consumption..."
        )
