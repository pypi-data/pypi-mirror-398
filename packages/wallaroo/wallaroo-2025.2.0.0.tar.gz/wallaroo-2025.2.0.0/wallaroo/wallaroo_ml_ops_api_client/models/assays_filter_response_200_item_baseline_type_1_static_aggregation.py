from enum import Enum


class AssaysFilterResponse200ItemBaselineType1StaticAggregation(str, Enum):
    CUMULATIVE = "Cumulative"
    DENSITY = "Density"
    EDGES = "Edges"

    def __str__(self) -> str:
        return str(self.value)
