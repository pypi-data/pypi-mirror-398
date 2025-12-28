from enum import Enum


class OrchestrationStatus(str, Enum):
    ERROR = "error"
    PACKAGING = "packaging"
    PENDING_PACKAGING = "pending_packaging"
    READY = "ready"
    UNINITIALIZED = "uninitialized"

    def __str__(self) -> str:
        return str(self.value)
