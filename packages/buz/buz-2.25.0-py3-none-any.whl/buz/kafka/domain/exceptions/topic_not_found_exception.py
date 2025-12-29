from __future__ import annotations


class TopicNotFoundException(Exception):
    def __init__(self, topic_name: str) -> None:
        super().__init__(f'The topic "{topic_name}", has not been found')
