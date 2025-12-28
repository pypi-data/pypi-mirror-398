from enum import Enum


class IntervalUnit(str, Enum):
    DAY = "Day"
    HOUR = "Hour"
    MINUTE = "Minute"
    WEEK = "Week"

    def __str__(self) -> str:
        return str(self.value)
