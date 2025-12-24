"""This module features the Inference interface, that can be used
as a blueprint to create concrete subclasses for performing inferences
on a model.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Set

from mac.exceptions import ModelNotAssignedError
from mac.types import InferenceData

logger = logging.getLogger(__name__)


class Inference(ABC):
    """This class specifies the interface for creating concrete inference classes,
    that can be used to calculate inferences on a model.

    Attributes:
        - expected_model_types: A set of model instance types
            that are expected by this inference.
        - model: The model on which the inference is calculated.
    """

    def __init__(self) -> None:
        """Initializes the Inference class."""
        self._model: Optional[Any] = None

    @property
    @abstractmethod
    def expected_model_types(self) -> Set[Any]:
        """Returns a set of model instance types that are expected by this inference.

        :return: A set of model instance types that are expected by this inference.
        """

    @property
    def model(self) -> Any:
        """Returns the model on which the inference is calculated.

        :return: The model on which the inference is calculated.
        """
        return self._model

    def predict(self, input_data: InferenceData) -> InferenceData:
        """Calculates the inference on the given input data.
        This function is a wrapper around the abstract _predict function,
        and makes sure that the model is assigned to the inference.

        :param input_data: The input data on which the inference is calculated.
        Depending on the number of inputs of the model, the input data
        can be either a single numpy array or a dictionary of numpy arrays.

        :raises ModelNotAssignedError: If the model is not assigned to the inference.

        :return: The output of the model. Depending on the number of outputs
        of the model, the output data can be either a single numpy array or
        a dictionary of numpy arrays.
        """
        self._raise_error_if_model_is_not_assigned()
        return self._predict(input_data)

    @abstractmethod
    def _predict(self, input_data: InferenceData) -> InferenceData:
        """Calculates the inference on the given input data.
        This is the core function that each subclass needs to implement
        in order to calculate the inference.

        :param input_data: The input data on which the inference is calculated.
        Depending on the number of inputs of the model, the input data can be
        either a single numpy array or a dictionary of numpy arrays.

        :raises InferenceDataValidationError: If the input data is not valid.
        Ideally, every subclass should raise this error if the input data is not valid.

        :return: The output of the model. Depending on the number of outputs
        of the model, the output data can be either a single numpy array or
        a dictionary of numpy arrays.
        """

    def _raise_error_if_model_is_not_assigned(self) -> None:
        """Raises a custom error if the model is not assigned to the inference.
        If self._model None, then a ModelNotAssignedError is raised.

        :raises ModelNotAssignedError: If the model is not assigned to the inference.
        """
        if self.model is None:
            message = "The model is not assigned to the Inference object."
            logger.error(message)
            raise ModelNotAssignedError(message)

    def _raise_error_if_model_is_wrong_type(self, model: Any) -> None:
        """Raises a custom error if the model is not of the expected type.
        If the model is not of the expected type, then a TypeError is raised.

        :param model: The model to check its type.

        :raises TypeError: If the model is not the expected type.
        """
        if not any(
            isinstance(model, model_type) for model_type in self.expected_model_types
        ):
            model_types = [
                model_type.__name__ for model_type in self.expected_model_types
            ]
            message = (
                f"The model is not of type(s): {model_types}. "
                f"Got type '{type(model).__name__}' instead."
            )
            logger.error(message)
            raise TypeError(message)
