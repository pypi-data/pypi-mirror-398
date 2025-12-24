"""This module features the StreamlinedInference class, that extends
the Inference interface, and can be used to run end-to-end inference
on a wrapped Inference subclass.
"""

import logging

# pylint: disable=protected-access
from typing import Any

from mac.inference.inference import Inference
from mac.io.data_validation import KeysValidator
from mac.types import InferenceData

logger = logging.getLogger(__name__)


class StreamlinedMLInference(Inference):
    """This class extends the Inference interface, and can be used
    to run inference on a ML framework (i.e. Sklearn). It is following
    the decorator pattern
    (more info here: https://refactoring.guru/design-patterns/decorator)
    and is supposed to be composed with an Inference implementation.

    Attributes:
        - expected_model_types: A set of model instance types that are expected
            by this inference.
        - wrappee: The Inference subclass that is wrapped
            by this StreamlinedInference.
        - data_validator: A DataValidator instance that is used to validate
            the input data.
    """

    def __init__(
        self,
        wrappee: Inference,
        data_validator: KeysValidator,
    ) -> None:
        self._wrappee = wrappee
        self._data_validator = data_validator
        super().__init__()

    @property
    def expected_model_types(self) -> set:
        return self._wrappee.expected_model_types

    @property
    def model(self) -> Any:
        """Returns the model on which the inference is calculated.

        :return: The model on which the inference is calculated.
        """
        return self._wrappee.model

    @model.setter
    def model(self, model: Any) -> None:
        self._wrappee.model = model  # type: ignore

    def _predict(self, input_data: InferenceData) -> InferenceData:
        """Calculates the inference on the given input data.
        This is the core function that each subclass needs to implement
        in order to calculate the inference.

        :param input_data: The input data on which the inference is calculated.
        Depending on the number of inputs of the model, the input data can be either
        a single numpy array or a dictionary of numpy arrays.
        It is important to note that in the case of TorchInference numpy array(s)
        should be of type float32.

        :raises InferenceDataValidationError: If the input data is not valid.
        Ideally, every subclass should raise this error if the input data is not valid.

        :return: The output of the model.
        """
        logger.info("Starting inference...")

        logger.info("Validating InferenceData...")
        self._data_validator.validate(data=input_data)  # type: ignore

        logger.info("Getting predictions...")
        predictions = self._wrappee._predict(input_data)

        logger.info("Inference finished.")

        return predictions
