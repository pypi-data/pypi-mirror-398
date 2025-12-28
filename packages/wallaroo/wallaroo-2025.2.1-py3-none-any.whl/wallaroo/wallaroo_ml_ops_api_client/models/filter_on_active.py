from enum import Enum


class FilterOnActive(str, Enum):
    ACTIVEONLY = "ActiveOnly"
    ALL = "All"
    INACTIVEONLY = "InactiveOnly"

    def __str__(self) -> str:
        return str(self.value)
