class HandlerNotRegisteredException(Exception):
    def __init__(self, handler_id: str):
        self.handler_id = handler_id
        super().__init__(f"Handler with id {handler_id} has not been registered and cannot be unregistered")
