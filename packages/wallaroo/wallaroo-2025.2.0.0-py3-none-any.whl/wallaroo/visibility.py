from enum import Enum


class _Visibility(str, Enum):
    """Represents the visibility of a Model or Pipeline"""

    PRIVATE = "private"
    PUBLIC = "public"
    GROUP = "group"

    @staticmethod
    def from_str(label: str):
        """Creates a Visibility from a str"""
        label = label.lower()
        if label == "private":
            return _Visibility.PRIVATE
        elif label == "public":
            return _Visibility.PUBLIC
        else:
            raise NotImplementedError
