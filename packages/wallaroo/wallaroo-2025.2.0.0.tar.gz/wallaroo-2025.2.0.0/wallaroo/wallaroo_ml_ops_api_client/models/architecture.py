from enum import Enum


class Architecture(str, Enum):
    ARM = "arm"
    POWER10 = "power10"
    X86 = "x86"

    def __str__(self) -> str:
        return str(self.value)
