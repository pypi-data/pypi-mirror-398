from __future__ import annotations


class KafkaTopicsAlreadyCreatedException(Exception):
    def __init__(self, topic_names: list[str]) -> None:
        self.topic_names = topic_names

        topics_messages = ",".join(self.topic_names)
        super().__init__(f"The topics ${topics_messages} are already created in the cluster")
