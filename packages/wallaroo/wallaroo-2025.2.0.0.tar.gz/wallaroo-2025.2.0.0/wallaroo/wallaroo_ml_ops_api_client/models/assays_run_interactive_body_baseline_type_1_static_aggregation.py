from enum import Enum


class AssaysRunInteractiveBodyBaselineType1StaticAggregation(str, Enum):
    CUMULATIVE = "Cumulative"
    DENSITY = "Density"
    EDGES = "Edges"

    def __str__(self) -> str:
        return str(self.value)
