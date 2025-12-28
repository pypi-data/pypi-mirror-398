from enum import Enum


class PythonVersion(str, Enum):
    VALUE_0 = "3.8"
    VALUE_1 = "3.9"

    def __str__(self) -> str:
        return str(self.value)
