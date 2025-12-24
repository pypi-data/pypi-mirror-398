from enum import Enum


class AccelerationType2(str, Enum):
    JETSON = "jetson"

    def __str__(self) -> str:
        return str(self.value)
