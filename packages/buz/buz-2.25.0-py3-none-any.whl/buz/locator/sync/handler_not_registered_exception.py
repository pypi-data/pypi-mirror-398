from buz import Handler


class HandlerNotRegisteredException(Exception):
    def __init__(self, handler: Handler):
        self.handler = handler
        super().__init__("Handler has not been registered and cannot be unregistered")
