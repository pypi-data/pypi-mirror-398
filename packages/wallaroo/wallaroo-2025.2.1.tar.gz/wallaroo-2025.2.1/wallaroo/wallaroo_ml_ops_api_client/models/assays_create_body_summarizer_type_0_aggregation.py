from enum import Enum


class AssaysCreateBodySummarizerType0Aggregation(str, Enum):
    CUMULATIVE = "Cumulative"
    DENSITY = "Density"
    EDGES = "Edges"

    def __str__(self) -> str:
        return str(self.value)
