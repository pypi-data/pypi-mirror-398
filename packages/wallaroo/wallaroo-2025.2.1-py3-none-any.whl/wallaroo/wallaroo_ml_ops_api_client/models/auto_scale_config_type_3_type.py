from enum import Enum


class AutoScaleConfigType3Type(str, Enum):
    NONE = "none"

    def __str__(self) -> str:
        return str(self.value)
