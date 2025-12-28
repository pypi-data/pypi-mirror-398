from enum import Enum


class UserType(str, Enum):
    """Represents a workspace user's role."""

    OWNER = "owner"
    COLLABORATOR = "collaborator"

    @staticmethod
    def from_str(label: str):
        """Creates a UserType from a str"""
        label = label.lower()
        if label == "collaborator":
            return UserType.COLLABORATOR
        elif label == "owner":
            return UserType.OWNER
        else:
            raise NotImplementedError
