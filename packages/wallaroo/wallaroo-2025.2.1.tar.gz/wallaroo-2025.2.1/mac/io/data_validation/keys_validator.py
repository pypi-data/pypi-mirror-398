"""This module features the AscendingKeysValidator class."""

import logging
from typing import Set

from pydata_util.decorators import log_error

from mac.exceptions import InferenceDataValidationError
from mac.io.data_validation.data_validator import DataValidator
from mac.types import InferenceData

logger = logging.getLogger(__name__)


class KeysValidator(DataValidator):
    """This class implements a data validator that checks if a set of
    keys match the expected keys.

    Attributes:
        - expected_keys: The expected keys.
    """

    def __init__(self, expected_keys: Set[str]) -> None:
        """Initialize the KeysValidator."""
        self.expected_keys = expected_keys

    @log_error(
        InferenceDataValidationError,
        "An error occurred during data validation.",
    )
    def validate(self, data: InferenceData) -> None:
        """Validate the given InferenceData.

        :param data: The data to validate.

        :raises InferenceDataValidationError: If the data is invalid.
        """

        data_keys = set(data.keys())

        if data_keys != self.expected_keys:
            message = f"Expected keys: {self.expected_keys}, got: {data_keys}"
            logger.error(message)
            raise InferenceDataValidationError(message)
        return
