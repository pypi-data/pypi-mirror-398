from enum import Enum


class FrameworkConfigType1Framework(str, Enum):
    CUSTOM = "custom"

    def __str__(self) -> str:
        return str(self.value)
