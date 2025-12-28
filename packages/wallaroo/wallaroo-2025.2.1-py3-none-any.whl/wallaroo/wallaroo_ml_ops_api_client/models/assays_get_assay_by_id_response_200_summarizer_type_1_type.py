from enum import Enum


class AssaysGetAssayByIdResponse200SummarizerType1Type(str, Enum):
    MULTIVARIATECONTINUOUS = "MultivariateContinuous"

    def __str__(self) -> str:
        return str(self.value)
