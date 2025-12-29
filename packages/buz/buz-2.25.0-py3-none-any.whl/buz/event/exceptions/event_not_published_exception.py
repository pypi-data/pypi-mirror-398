from buz.event import Event


class EventNotPublishedException(Exception):
    def __init__(self, event: Event) -> None:
        self.event = event
        super().__init__(f"Event could not be published: {event}")
