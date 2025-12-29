class HandlerFqnNotFoundException(Exception):
    def __init__(self, handler_fqn: str):
        self.handler_fqn = handler_fqn
        super().__init__(f"Handler with fqn {handler_fqn} has not been found")
