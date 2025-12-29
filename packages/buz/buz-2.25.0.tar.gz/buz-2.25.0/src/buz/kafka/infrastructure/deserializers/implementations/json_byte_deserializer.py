from __future__ import annotations

import json

from buz.kafka.infrastructure.deserializers.byte_deserializer import ByteDeserializer


class JSONByteDeserializer(ByteDeserializer[dict]):
    __STRING_ENCODING = "utf-8"

    def deserialize(self, data: bytes) -> dict:
        decoded_string = data.decode(self.__STRING_ENCODING)
        return json.loads(decoded_string)
