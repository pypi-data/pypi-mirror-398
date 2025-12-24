from enum import Enum


class AccelerationType1(str, Enum):
    CUDA = "cuda"

    def __str__(self) -> str:
        return str(self.value)
