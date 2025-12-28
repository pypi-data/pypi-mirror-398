from enum import Enum


class ModelStatus(str, Enum):
    ATTEMPTING_LOAD_CONTAINER = "attempting_load_container"
    ATTEMPTING_LOAD_NATIVE = "attempting_load_native"
    ERROR = "error"
    PENDING_LOAD_CONTAINER = "pending_load_container"
    PENDING_LOAD_NATIVE = "pending_load_native"
    READY = "ready"
    UPLOADING = "uploading"

    def __str__(self) -> str:
        return str(self.value)
