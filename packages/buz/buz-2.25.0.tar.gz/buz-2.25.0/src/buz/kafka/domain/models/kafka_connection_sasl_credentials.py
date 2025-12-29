from __future__ import annotations

from dataclasses import dataclass

from buz.kafka.domain.models.kafka_connection_credentials import KafkaConnectionCredentials
from buz.kafka.domain.models.kafka_supported_sasl_mechanisms import KafkaSupportedSaslMechanisms
from buz.kafka.domain.models.kafka_supported_security_protocols import KafkaSupportedSecurityProtocols


@dataclass(frozen=True)
class KafkaConnectionSaslCredentials(KafkaConnectionCredentials):
    security_protocol: KafkaSupportedSecurityProtocols
    user: str
    password: str
    sasl_mechanism: KafkaSupportedSaslMechanisms
