from enum import Enum


class AccelerationType0(str, Enum):
    NONE = "none"

    def __str__(self) -> str:
        return str(self.value)
