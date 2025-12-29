class HandlerNotFoundException(Exception):
    def __init__(self, handler_id: str):
        self.handler_id = handler_id
        super().__init__(f"Handler with id {handler_id} has not been found in the container and cannot be registered")
