from enum import Enum


class KafkaSupportedSecurityProtocols(Enum):
    PLAINTEXT = "PLAINTEXT"
    SASL_PLAINTEXT = "SASL_PLAINTEXT"
    SASL_SSL = "SASL_SSL"
