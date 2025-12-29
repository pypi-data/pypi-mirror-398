from buz import Handler


class HandlerAlreadyRegisteredException(Exception):
    def __init__(self, handler: Handler):
        self.handler = handler
        super().__init__("Handler has been registered and cannot be registered another time")
