"""This module defines Service interface. All inference services must
implement this interface, e.g., MLflowService.
"""

from abc import ABC, abstractmethod


class Service(ABC):
    """Abstract class for an Inference service."""

    @abstractmethod
    def serve(self) -> None:
        """This method serves an Inference object using a service."""
