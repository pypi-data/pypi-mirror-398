from enum import Enum


class KafkaSupportedSaslMechanisms(Enum):
    PLAIN = "PLAIN"
    GSSAPI = "GSSAPI"
    OAUTHBEARER = "OAUTHBEARER"
    SCRAM_SHA_256 = "SCRAM-SHA-256"
    SCRAM_SHA_512 = "SCRAM-SHA-512"
