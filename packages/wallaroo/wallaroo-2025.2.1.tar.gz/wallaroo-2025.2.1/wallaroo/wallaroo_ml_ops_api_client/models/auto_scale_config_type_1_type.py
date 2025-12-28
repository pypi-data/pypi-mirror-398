from enum import Enum


class AutoScaleConfigType1Type(str, Enum):
    GPU = "gpu"

    def __str__(self) -> str:
        return str(self.value)
