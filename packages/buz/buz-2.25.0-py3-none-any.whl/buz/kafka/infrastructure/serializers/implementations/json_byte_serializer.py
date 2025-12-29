from __future__ import annotations

import json
from datetime import date, datetime, time
from enum import Enum
from typing import Any, Union

from buz.kafka.infrastructure.serializers.byte_serializer import ByteSerializer

STRING_ENCODING = "utf-8"

PRIMITIVES = Union[int, str, float, None, bool, datetime, date, time, Enum]

ALLOWED_SERIALIZABLE_DICTIONARY_KEYS = str

JSON_SERIALIZABLE_VALUE = Union[PRIMITIVES, list[PRIMITIVES], dict[ALLOWED_SERIALIZABLE_DICTIONARY_KEYS, PRIMITIVES]]

JSON_SERIALIZABLE = Union[
    dict[ALLOWED_SERIALIZABLE_DICTIONARY_KEYS, Union[JSON_SERIALIZABLE_VALUE, "JSON_SERIALIZABLE"]]
]


class JSONByteSerializer(ByteSerializer[JSON_SERIALIZABLE]):
    def serialize(self, data: JSON_SERIALIZABLE) -> bytes:
        json_object = self.serialize_as_json(data)
        encoded_string = bytes(
            json_object,
            STRING_ENCODING,
        )

        return encoded_string

    def serialize_as_json(self, data: JSON_SERIALIZABLE) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            default=lambda value: self.__json_serial(value),
        )

    # @see https://stackoverflow.com/questions/11875770/how-can-i-overcome-datetime-datetime-not-json-serializable
    def __json_serial(self, obj: Any) -> Any:
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))
