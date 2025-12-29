from buz.kafka.domain.exceptions.not_valid_kafka_message_exception import NotValidKafkaMessageException
from buz.kafka.infrastructure.cdc.cdc_payload import CDCPayload


class CannotRestoreEventFromCDCPayloadException(NotValidKafkaMessageException):
    def __init__(self, cdc_payload: CDCPayload, exception: Exception) -> None:
        self.exception = exception
        self.cdc_payload = cdc_payload
        super().__init__(
            f'Couldn\'t build a message from CDC payload "{self.cdc_payload}". Raised from "{str(exception)}"'
        )
