from enum import Enum


class FrameworkConfigType0Framework(str, Enum):
    VLLM = "vllm"

    def __str__(self) -> str:
        return str(self.value)
