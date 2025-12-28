from enum import Enum


class AutoScaleConfigType2Type(str, Enum):
    QUEUE = "queue"

    def __str__(self) -> str:
        return str(self.value)
