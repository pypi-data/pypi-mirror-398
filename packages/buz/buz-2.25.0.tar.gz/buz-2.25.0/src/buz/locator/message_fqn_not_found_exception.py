class MessageFqnNotFoundException(Exception):
    def __init__(self, message_fqn: str):
        self.message_fqn = message_fqn
        super().__init__(f"Message with fqn {message_fqn} has not been found")
