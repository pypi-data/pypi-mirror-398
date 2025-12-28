from enum import Enum


class AssaysGetAssayByIdResponse200SummarizerType0Aggregation(str, Enum):
    CUMULATIVE = "Cumulative"
    DENSITY = "Density"
    EDGES = "Edges"

    def __str__(self) -> str:
        return str(self.value)
