from enum import Enum


class KafkaSupportedCompressionType(Enum):
    GZIP = "gzip"
    SNAPPY = "snappy"
    LZ4 = "lz4"
    ZSTD = "zstd"
