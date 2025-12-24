"""This module features the DataValidator class."""

from __future__ import annotations

from abc import ABC, abstractmethod

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from mac.types import InferenceData


class DataValidator(ABC):
    """This class can be used as a blueprint to create concrete data validators.
    It can be used for validating InferenceData in order to make sure
    that it is valid for a specific model."""

    @abstractmethod
    def validate(self, data: InferenceData) -> None:
        """This method should be implemented by subclasses to validate the
        given InferenceData.

        :param data: The data to validate.

        :raises InferenceDataValidationError: If the data is invalid.
        """
