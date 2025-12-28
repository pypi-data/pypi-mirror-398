from enum import Enum


class AssaysFilterBodySortBy(str, Enum):
    CREATIONDATEDESC = "CreationDateDesc"
    LASTRUNDATEDESC = "LastRunDateDesc"

    def __str__(self) -> str:
        return str(self.value)
