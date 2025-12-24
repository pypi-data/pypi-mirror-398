from enum import Enum


class StatusGetDeploymentResponse200EngineLbsItemInfoStatus(str, Enum):
    FAILED = "Failed"
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    UNKNOWN = "Unknown"

    def __str__(self) -> str:
        return str(self.value)
