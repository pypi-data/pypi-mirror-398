from __future__ import annotations

from buz.event.event import Event
from buz.kafka.infrastructure.serializers.implementations.json_byte_serializer import JSONByteSerializer
from buz.kafka.infrastructure.serializers.partitiion_key_generator import PartitionKeySerializer

# This is a static string because the order matters and we can not trust that json encoder libraries are deterministic
PAYLOAD_CDC_SCHEMA = r"""{"schema":{"type":"string","optional":true},"payload":"[partition_key]"}"""


class CDCPartitionKeySerializer(PartitionKeySerializer):
    def __init__(self) -> None:
        self.__json_serializer = JSONByteSerializer()

    def __generate_payload_schema(self, partition_key: str) -> str:
        return PAYLOAD_CDC_SCHEMA.replace("[partition_key]", partition_key)

    def generate_key(self, event: Event) -> str:
        return self.__generate_payload_schema(event.partition_key())
