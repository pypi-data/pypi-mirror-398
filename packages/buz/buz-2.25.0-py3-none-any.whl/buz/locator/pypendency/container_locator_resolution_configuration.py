from logging import Logger
from typing import Optional


class ContainerLocatorResolutionConfiguration:
    def __init__(self, allow_partial_resolve: bool, logger: Optional[Logger] = None):
        if allow_partial_resolve is True and logger is None:
            raise ValueError("Logger cannot be None with partial resolution enabled")

        self.allow_partial_resolve = allow_partial_resolve
        self.logger = logger
