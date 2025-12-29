from buz.kafka.domain.exceptions.not_valid_kafka_message_exception import NotValidKafkaMessageException


class CannotDecodeCDCMessageException(NotValidKafkaMessageException):
    def __init__(self, message: str, exception: Exception) -> None:
        self.exception = exception
        self.message = message
        super().__init__(f'The CDC message "{self.message}" was not decoded correctly: "{str(exception)}"')
