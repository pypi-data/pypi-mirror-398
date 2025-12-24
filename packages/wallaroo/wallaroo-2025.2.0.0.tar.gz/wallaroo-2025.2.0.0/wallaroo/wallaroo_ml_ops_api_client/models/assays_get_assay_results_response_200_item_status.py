from enum import Enum


class AssaysGetAssayResultsResponse200ItemStatus(str, Enum):
    ALERT = "Alert"
    BASELINERUN = "BaselineRun"
    OK = "Ok"
    WARNING = "Warning"

    def __str__(self) -> str:
        return str(self.value)
