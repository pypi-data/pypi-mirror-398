from enum import Enum


class DataSizeUnit(Enum):
    """Data size limits for exported pipeline log files"""

    KiB = "KiB"
    MiB = "MiB"
    GiB = "GiB"
    TiB = "TiB"

    @staticmethod
    def from_string(unit_str):
        for unit in DataSizeUnit:
            if unit.value == unit_str:
                return unit
        raise ValueError(
            f"Invalid data size unit {unit_str}. Please use one of: KiB, MiB, GiB, TiB"
        )

    def calculate_bytes(self, size):
        if self == DataSizeUnit.KiB:
            return size * 1024
        elif self == DataSizeUnit.MiB:
            return size * 1024**2
        elif self == DataSizeUnit.GiB:
            return size * 1024**3
        elif self == DataSizeUnit.TiB:
            return size * 1024**4
