from enum import Enum


class AccelerationType3(str, Enum):
    OPENVINO = "openvino"

    def __str__(self) -> str:
        return str(self.value)
