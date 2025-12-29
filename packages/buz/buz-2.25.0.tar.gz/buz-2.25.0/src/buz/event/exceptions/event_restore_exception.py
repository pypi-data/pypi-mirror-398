class EventRestoreException(Exception):
    def __init__(self, body: dict, message: str) -> None:
        self.body = body
        self.message = message
        super().__init__(f"Event could not be restored. Body: {body}. Message: {message}")
