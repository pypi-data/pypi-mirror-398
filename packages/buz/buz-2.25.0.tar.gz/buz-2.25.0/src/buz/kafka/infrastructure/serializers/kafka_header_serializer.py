from __future__ import annotations


STRING_ENCODING = "utf-8"


class KafkaHeaderSerializer:
    def serialize(self, headers: dict[str, str]) -> list[tuple[str, bytes]]:
        return [(key, self.__str_to_bytes(value)) for key, value in headers.items()]

    def deserialize(self, data: list[tuple[str, bytes]]) -> dict[str, str]:
        deserialized_data = [(key, self.__bytes_to_str(value)) for key, value in data]
        return dict(deserialized_data)

    def __str_to_bytes(self, data: str) -> bytes:
        return bytes(data, STRING_ENCODING)

    def __bytes_to_str(self, data: bytes) -> str:
        return data.decode(STRING_ENCODING)
