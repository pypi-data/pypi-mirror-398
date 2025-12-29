from typing import Any, TypedDict


class Metadata(TypedDict):
    def __init__(self, **kwargs: dict[str, Any]) -> None:  # type: ignore[misc]
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)
