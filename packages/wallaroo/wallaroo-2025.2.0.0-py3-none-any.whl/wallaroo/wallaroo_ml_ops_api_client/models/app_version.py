from enum import Enum


class AppVersion(str, Enum):
    VALUE_0 = "2024.1.0"
    VALUE_1 = "2024.1.5"
    VALUE_10 = "2024.4.0"
    VALUE_11 = "2024.4.1"
    VALUE_12 = "2024.4.2"
    VALUE_13 = "2024.4.3"
    VALUE_14 = "2024.4.4"
    VALUE_15 = "2025.1.0"
    VALUE_16 = "2025.1.1"
    VALUE_17 = "2025.1.2"
    VALUE_18 = "2025.1.3"
    VALUE_19 = "2025.1.4"
    VALUE_2 = "2024.2.0"
    VALUE_20 = "2025.2.0"
    VALUE_3 = "2024.2.1"
    VALUE_4 = "2024.2.2"
    VALUE_5 = "2024.2.3"
    VALUE_6 = "2024.3.0"
    VALUE_7 = "2024.3.1"
    VALUE_8 = "2024.3.2"
    VALUE_9 = "2024.3.3"

    def __str__(self) -> str:
        return str(self.value)
