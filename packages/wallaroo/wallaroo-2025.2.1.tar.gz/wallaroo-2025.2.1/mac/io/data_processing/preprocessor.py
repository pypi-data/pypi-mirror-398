"""This module features the Preprocessor interface that can be extended to
implement a custom data preprocessor for InferenceData."""

from abc import ABC, abstractmethod
from typing import Any

from mac.types import InferenceData


class Preprocessor(ABC):
    """This class serves as an interface for creating concrete data preprocessors."""

    @abstractmethod
    def preprocess(self, data: InferenceData) -> Any:
        """Preprocess the incoming InferenceData. The purpose of this method
        is to be used within any Inference subclass that requires transforming
        InferenceData to framework-specific model input.

        :param data: Data to preprocess.

        :return: Preprocessed data.
        """
