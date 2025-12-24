from enum import Enum


class ExecTypeType0(str, Enum):
    JOB = "job"

    def __str__(self) -> str:
        return str(self.value)
