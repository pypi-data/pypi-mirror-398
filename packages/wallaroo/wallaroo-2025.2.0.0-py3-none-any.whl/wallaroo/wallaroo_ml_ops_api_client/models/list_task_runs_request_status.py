from enum import Enum


class ListTaskRunsRequestStatus(str, Enum):
    ALL = "all"
    FAILURE = "failure"
    RUNNING = "running"
    SUCCESS = "success"
    TIMED_OUT = "timed_out"

    def __str__(self) -> str:
        return str(self.value)
