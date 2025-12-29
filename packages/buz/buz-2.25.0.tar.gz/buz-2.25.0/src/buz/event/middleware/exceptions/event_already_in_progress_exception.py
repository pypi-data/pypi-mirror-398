class EventAlreadyInProgressException(Exception):
    def __init__(self, event_id: str, subscriber_fqn: str) -> None:
        self.event_id = event_id
        self.subscriber_fqn = subscriber_fqn
        super().__init__(f"Event {event_id} is already in progress by subscriber {subscriber_fqn}")
