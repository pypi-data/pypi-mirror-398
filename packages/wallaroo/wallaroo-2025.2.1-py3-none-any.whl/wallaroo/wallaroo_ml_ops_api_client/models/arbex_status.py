from enum import Enum


class ArbexStatus(str, Enum):
    CRASH_LOOP = "crash_loop"
    FAILED = "failed"
    KILLED = "killed"
    PAUSED = "paused"
    PENDING = "pending"
    PENDING_KILL = "pending_kill"
    PENDING_PAUSE = "pending_pause"
    PENDING_RESUME = "pending_resume"
    RESOURCE_CONTENTION = "resource_contention"
    SCHEDULE_ERROR = "schedule_error"
    STARTED = "started"
    SUCCESS = "success"
    TIMED_OUT = "timed_out"

    def __str__(self) -> str:
        return str(self.value)
