class InvalidMaxRetriesParamException(Exception):
    def __init__(self, max_retries: int) -> None:
        self.max_retries = max_retries
        super().__init__(f"Max retries cannot be negative, provided value: {max_retries}")
