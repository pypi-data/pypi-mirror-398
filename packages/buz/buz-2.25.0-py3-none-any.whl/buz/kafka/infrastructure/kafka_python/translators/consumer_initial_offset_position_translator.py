from buz.kafka.domain.models.consumer_initial_offset_position import ConsumerInitialOffsetPosition


class KafkaPythonConsumerInitialOffsetPositionTranslator:
    @classmethod
    def to_kafka_supported_format(cls, consumer_initial_offset_position: ConsumerInitialOffsetPosition) -> str:
        if consumer_initial_offset_position == ConsumerInitialOffsetPosition.BEGINNING:
            return "earliest"
        if consumer_initial_offset_position == ConsumerInitialOffsetPosition.END:
            return "latest"

        raise ValueError(f"Invalid ConsumerInitialOffsetPosition: {consumer_initial_offset_position}")
