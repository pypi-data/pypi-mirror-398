from enum import Enum


class KafkaOnFailStrategy(str, Enum):
    STOP_ON_FAIL = "stop_on_fail"
    CONSUME_ON_FAIL = "consume_on_fail"
