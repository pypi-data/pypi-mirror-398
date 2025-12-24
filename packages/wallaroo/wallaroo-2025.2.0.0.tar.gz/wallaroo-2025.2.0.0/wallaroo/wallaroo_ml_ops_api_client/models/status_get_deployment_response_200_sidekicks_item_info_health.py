from enum import Enum


class StatusGetDeploymentResponse200SidekicksItemInfoHealth(str, Enum):
    ERROR = "Error"
    RUNNING = "Running"
    STARTING = "Starting"

    def __str__(self) -> str:
        return str(self.value)
