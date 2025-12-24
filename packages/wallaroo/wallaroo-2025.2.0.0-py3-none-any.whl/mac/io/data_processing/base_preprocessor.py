"""This module features the BasePreprocessor interface that can be extended to
implement a concrete data preprocessor for InferenceData and covers the use-case
where the user sends the data with the pre-agreed contract of ascending input
keys."""

import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional

import numpy.typing as npt
from pydantic import BaseModel, ConfigDict, StrictStr
from pydata_util.decorators import log_error

from mac.exceptions import InferencePreprocessingError
from mac.io.data_processing.preprocessor import Preprocessor
from mac.types import InferenceData

logger = logging.getLogger(__name__)


class BasePreprocessor(Preprocessor, BaseModel):
    """This class serves as an interface for creating concrete data preprocessors,
    that preprocess data sent in the pre-agreed user contract
    (i.e. ascending input keys) and returns the data in a framework-appropriate format.

    Attributes:
        - expected_keys: Expected keys of the data.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        validate_assignment=True,
    )

    expected_keys: Optional[List[StrictStr]] = None

    @abstractmethod
    def _convert_inference_data_to_model_inputs(
        self, data: Dict[str, npt.NDArray]
    ) -> Any:
        """Convert a dictionary of arrays to model inputs."""

    @log_error(
        InferencePreprocessingError,
        "An error occurred during pre-processing.",
    )
    def preprocess(self, data: InferenceData) -> Any:
        """Preprocess the incoming InferenceData to model inputs.

        :param data: Data to preprocess.

        :return: Preprocessed data.
        """
        self._raise_error_if_expected_keys_is_none()
        data_ = data.copy()

        if is_key_order_incorrect(data, self.expected_keys):  # type: ignore
            data_ = self._rearrange_input_order(data)

        return self._convert_inference_data_to_model_inputs(data_)

    def _raise_error_if_expected_keys_are_wrong_type(self, value: Any) -> None:
        """Raise an error if the expected keys are of wrong type."""

        if not isinstance(value, list) or (
            isinstance(value, list) and not all(isinstance(key, str) for key in value)
        ):
            message = "Expected keys must be a list of strings."
            logger.error(message)
            raise TypeError(message)

    def _rearrange_input_order(
        self,
        input_data: Dict[str, npt.NDArray],
    ) -> Dict[str, npt.NDArray]:
        return {key: input_data[key] for key in self.expected_keys}  # type: ignore

    def _raise_error_if_expected_keys_is_none(self) -> None:
        if self.expected_keys is None:
            message = "Expected keys must be set."
            logger.error(message)
            raise ValueError(message)


def is_key_order_incorrect(data: Dict[str, Any], expected_keys: list) -> bool:
    """Checks if the keys of the given dictionary are in the correct order.

    :param data: The dictionary to check.
    :param expected_keys: The expected keys of the dictionary.

    :return: True if the keys of the given dictionary are in the correct order,
        False otherwise.
    """
    return list(data.keys()) != expected_keys
