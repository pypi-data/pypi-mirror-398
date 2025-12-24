"""This module features the implementation of the InferenceBuilder
for generating Inference subclass instances from a given AutoInferenceConfig.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydata_util.nats.framework_config import CustomConfig

from mac.config.python_step import PythonStepConfig
from mac.inference.inference import Inference


class InferenceBuilder(ABC):
    """This class implements the InferenceBuilder implementation
    for generating Inference subclass instances given an `PythonStepConfig`.

    Attributes:
        - custom_config: A `CustomConfig` instance that is included in the NATS
            message.
    """

    def __init__(self):
        self._custom_config: Optional[CustomConfig] = None

    @property
    def custom_config(self) -> Optional[CustomConfig]:
        """Returns the `CustomConfig`.

        :return: A `CustomConfig` instance.
        """
        return self._custom_config

    @custom_config.setter
    def custom_config(self, value: Any) -> None:
        """Sets the `CustomConfig`.

        :param value: A `CustomConfig` instance.

        :raises ValueError: If `value` is not of type `CustomConfig`.
        """
        if not isinstance(value, CustomConfig):
            raise ValueError("`custom_config` must be of type `CustomConfig`")
        self._custom_config = value

    @property
    @abstractmethod
    def inference(self) -> Inference:
        """Returns an Inference subclass instance.
        This specifies the Inference instance to be used
        by create() to build additionally needed components."""

    @abstractmethod
    def create(self, config: PythonStepConfig) -> Inference:
        """Creates an Inference subclass and assigns a model to it.

        :param config: Inference configuration.

        :return: Inference subclass
        """
