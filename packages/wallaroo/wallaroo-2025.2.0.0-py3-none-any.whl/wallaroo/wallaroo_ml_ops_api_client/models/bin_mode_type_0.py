from enum import Enum


class BinModeType0(str, Enum):
    NONE = "None"

    def __str__(self) -> str:
        return str(self.value)
