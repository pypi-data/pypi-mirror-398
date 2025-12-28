from enum import Enum


class AssayStatus(str, Enum):
    ALERT = "Alert"
    OK = "Ok"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)
