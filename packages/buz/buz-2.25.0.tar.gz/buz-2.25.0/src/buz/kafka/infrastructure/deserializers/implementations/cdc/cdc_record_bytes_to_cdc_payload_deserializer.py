from __future__ import annotations

import orjson
from cachetools import LRUCache
from dacite import from_dict

from buz.kafka.infrastructure.cdc.cdc_message import CDCPayload
from buz.kafka.infrastructure.deserializers.implementations.cdc.cannot_decode_cdc_message_exception import (
    CannotDecodeCDCMessageException,
)


class CDCRecordBytesToCDCPayloadDeserializer:
    __STRING_ENCODING = "utf-8"
    __cached_deserialization: LRUCache[str, CDCPayload] = LRUCache(maxsize=128)

    def deserialize(self, data: bytes) -> CDCPayload:
        decoded_string = data.decode(self.__STRING_ENCODING)
        if decoded_string not in CDCRecordBytesToCDCPayloadDeserializer.__cached_deserialization:
            try:
                CDCRecordBytesToCDCPayloadDeserializer.__cached_deserialization[
                    decoded_string
                ] = self.__get_cdc_payload_from_string(decoded_string)
            except Exception as exception:
                raise CannotDecodeCDCMessageException(decoded_string, exception) from exception

        return CDCRecordBytesToCDCPayloadDeserializer.__cached_deserialization[decoded_string]

    def __get_cdc_payload_from_string(self, decoded_string: str) -> CDCPayload:
        decoded_record: dict = orjson.loads(decoded_string)
        payload = decoded_record.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("The provided payload value is not valid")

        return from_dict(CDCPayload, payload)
