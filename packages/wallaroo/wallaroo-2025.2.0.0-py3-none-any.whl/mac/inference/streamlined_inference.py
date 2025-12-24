"""This module features the StreamlinedInference class, that extends
the Inference interface, and can be used to run end-to-end inference
on a wrapped Inference subclass.
"""

import logging

# pylint: disable=protected-access
from abc import abstractmethod
from typing import Any

from mac.inference.inference import Inference
from mac.io.data_processing import Postprocessor, Preprocessor
from mac.io.data_validation import DataValidator
from mac.types import InferenceData

logger = logging.getLogger(__name__)


class StreamlinedInference(Inference):
    """This class extends the Inference interface, and can be used
    to run inference on a DL framework. It is following the decorator pattern
    (more info here: https://refactoring.guru/design-patterns/decorator)
    and is supposed to be composed with an Inference implementation.

    Attributes:
        - expected_model_types: A set of model instance types that are expected
            by this inference.
        - wrappee: The Inference subclass that is wrapped by this StreamlinedInference.
        - data_validator: A DataValidator instance that is used to validate
            the input data.
        - preprocessor: A Preprocessor instance that is used to preprocess
            the input data.
        - postprocessor: A Postprocessor instance that is used to postprocess
            the output data.
    """

    def __init__(
        self,
        wrappee: Inference,
        preprocessor: Preprocessor,
        postprocessor: Postprocessor,
        data_validator: DataValidator,
    ) -> None:
        self._wrappee = wrappee
        self._preprocessor = preprocessor
        self._postprocessor = postprocessor
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
        a single numpy array or a dictionary of numpy arrays. It is important to note
        that in the case of TorchInference numpy array(s) should be of type float32.

        :raises InferenceDataValidationError: If the input data is not valid.
        Ideally, every subclass should raise this error if the input data is not valid.

        :return: The output of the model. Depending on the number of outputs
        of the model, the output data can be either a single numpy array or
        a dictionary of numpy arrays.
        """
        logger.info("Starting inference...")

        logger.info("Validating InferenceData...")
        self._data_validator.validate(data=input_data)  # type: ignore

        logger.info("Preprocessing InferenceData...")
        input_data_ = self._preprocess(input_data)

        logger.info("Getting predictions...")
        predictions = self._wrappee._predict(input_data_)

        logger.info("Postprocessing predictions...")
        predictions = self._postprocess(predictions)

        logger.info("Inference finished.")

        return predictions

    @abstractmethod
    def _preprocess(self, data: InferenceData) -> Any:
        """Preprocess the input data if data is multi-output."""

    def _postprocess(self, data: Any) -> InferenceData:
        """Postprocess inferences."""
        self._postprocessor.data = data
        with self._postprocessor.postprocess() as data_:
            return data_
