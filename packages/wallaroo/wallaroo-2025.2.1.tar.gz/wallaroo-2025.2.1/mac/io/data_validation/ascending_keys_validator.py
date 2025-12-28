"""This module features the AscendingKeysValidator class."""

import logging
from typing import List, Optional

from pydata_util.decorators import log_error

from mac.exceptions import InferenceDataValidationError
from mac.io.data_validation.data_validator import DataValidator
from mac.types import InferenceData

logger = logging.getLogger(__name__)


class AscendingKeysValidator(DataValidator):
    """This class implements a data validator that checks if the key names are
    consisted of a skeleton that increases in ascending order.

    Example:

    data = {"input_1": ..., "input_2", ..., "input_3", ...}

    Attributes:
        - expected_skeleton: The expected skeleton of the keys.
        - expected_keys: The expected keys.
    """

    def __init__(self, expected_skeleton: str) -> None:
        """Initialize the AscendingKeysValidator."""
        self.expected_skeleton = expected_skeleton
        self.expected_keys: Optional[List] = None

    @log_error(
        InferenceDataValidationError,
        "An error occurred during data validation.",
    )
    def validate(self, data: InferenceData) -> None:
        """Validate the given InferenceData.

        :param data: The data to validate.

        :raises InferenceDataValidationError: If the data is invalid.
        """

        data_keys = list(data.keys())
        self._get_expected_keys(len(data_keys))

        if len(data_keys) == 1:
            if data_keys != self.expected_keys:
                message = f"Expected keys: {self.expected_keys}, got: {data_keys}"
                logger.error(message)
                raise InferenceDataValidationError(message)
            return

        if set(data_keys) != set(self.expected_keys):  # type: ignore
            message = f"Expected keys: {self.expected_keys}, got: {data_keys}"
            logger.error(message)
            raise InferenceDataValidationError(message)
        return

    def _get_expected_keys(self, len_data: int) -> None:
        if len_data == 1:
            self.expected_keys = [self.expected_skeleton]
        else:
            self.expected_keys = [
                self.expected_skeleton + "_" + str(i) for i in range(1, len_data + 1)
            ]
