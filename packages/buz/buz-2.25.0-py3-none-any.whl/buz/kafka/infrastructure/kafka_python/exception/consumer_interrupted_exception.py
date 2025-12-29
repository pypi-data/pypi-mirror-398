class ConsumerInterruptedException(Exception):
    def __init__(self):
        message = "The consumer execution was interrupted"
        super().__init__(message)
