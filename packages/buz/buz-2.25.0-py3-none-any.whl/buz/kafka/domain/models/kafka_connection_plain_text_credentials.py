from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from buz.kafka.domain.models.kafka_connection_credentials import KafkaConnectionCredentials
from buz.kafka.domain.models.kafka_supported_security_protocols import KafkaSupportedSecurityProtocols


@dataclass(frozen=True)
class KafkaConnectionPlainTextCredentials(KafkaConnectionCredentials):
    security_protocol: Literal[KafkaSupportedSecurityProtocols.PLAINTEXT] = KafkaSupportedSecurityProtocols.PLAINTEXT
    user: None = None
    password: None = None
    sasl_mechanism: None = None
