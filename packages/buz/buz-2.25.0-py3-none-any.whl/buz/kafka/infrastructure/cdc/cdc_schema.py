from buz.message import Message


def generate_cdc_schema(message: Message) -> dict:
    return {
        "type": "struct",
        "fields": [
            {
                "type": "string",
                "optional": False,
                "field": "payload",
            },
            {
                "type": "string",
                "optional": False,
                "name": "io.debezium.data.Uuid",
                "version": 1,
                "field": "event_id",
            },
            {
                "type": "string",
                "optional": False,
                "field": "event_fqn",
            },
            {
                "type": "string",
                "optional": True,
                "name": "io.debezium.data.Json",
                "version": 1,
                "field": "metadata",
            },
            {
                "type": "string",
                "optional": False,
                "name": "io.debezium.time.ZonedTimestamp",
                "version": 1,
                "field": "created_at",
            },
        ],
        "optional": False,
        "name": f"{message.fqn()}.Value",
    }
