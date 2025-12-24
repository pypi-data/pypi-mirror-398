from enum import Enum


class KvCacheDtype(str, Enum):
    AUTO = "auto"
    FP8 = "fp8"
    FP8_E4M3 = "fp8_e4m3"
    FP8_E5M2 = "fp8_e5m2"
    MXINT8 = "mxint8"

    def __str__(self) -> str:
        return str(self.value)
