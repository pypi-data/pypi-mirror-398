from enum import Enum


class AssaysFilterResponse200ItemSummarizerType0BinMode(str, Enum):
    EQUAL = "Equal"
    NONE = "None"
    PROVIDED = "Provided"
    QUANTILE = "Quantile"

    def __str__(self) -> str:
        return str(self.value)
