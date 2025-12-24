from enum import Enum


class AutoScaleConfigType0Type(str, Enum):
    CPU = "cpu"

    def __str__(self) -> str:
        return str(self.value)
