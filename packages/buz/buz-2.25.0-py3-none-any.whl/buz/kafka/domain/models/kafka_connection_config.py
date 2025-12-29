from __future__ import annotations

from dataclasses import dataclass

from buz.kafka.domain.models.kafka_connection_credentials import KafkaConnectionCredentials


@dataclass(frozen=True)
class KafkaConnectionConfig:
    bootstrap_servers: list[str]
    client_id: str
    credentials: KafkaConnectionCredentials
