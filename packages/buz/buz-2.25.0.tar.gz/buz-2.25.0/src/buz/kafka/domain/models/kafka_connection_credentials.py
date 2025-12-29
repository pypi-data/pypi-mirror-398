from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Optional

from buz.kafka.domain.models.kafka_supported_sasl_mechanisms import KafkaSupportedSaslMechanisms
from buz.kafka.domain.models.kafka_supported_security_protocols import KafkaSupportedSecurityProtocols


@dataclass(frozen=True)
class KafkaConnectionCredentials(ABC):
    security_protocol: KafkaSupportedSecurityProtocols
    user: Optional[str]
    password: Optional[str]
    sasl_mechanism: Optional[KafkaSupportedSaslMechanisms]
