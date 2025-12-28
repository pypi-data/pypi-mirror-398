"""This module features the Postprocessor interface that can be extended to
implement a custom data postprocessor for InferenceData."""

import logging
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generator, Optional

from pydantic import BaseModel, ConfigDict

from mac.types import InferenceData

logger = logging.getLogger(__name__)


class Postprocessor(ABC, BaseModel):
    """This class serves as an interface for creating concrete data postprocessors.
    The data has to be passed during instantiation and can be accessed via the
    `data` attribute. The `_postprocess()` abstract method has to be implemented
    by the concrete subclass. The `postprocess()` method can be used as a context
    manager to postprocess the data and reset the data attribute once finished.

    Attributes:
        - data: Data to postprocess.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        validate_assignment=True,
    )

    data: Optional[Any] = None

    @abstractmethod
    def _postprocess(self) -> InferenceData:
        """Postprocess the data.

        :return: Postprocessed data.
        """

    @contextmanager
    def postprocess(self) -> Generator[InferenceData, None, None]:
        """Transform the incoming data to InferenceData.

        :return: Preprocessed data.
        """
        self._raise_error_if_data_is_none()

        yield self._postprocess()

        self.reset()

    def reset(self) -> None:
        """Reset the postprocessor data."""
        self.data = None

    def _raise_error_if_data_is_none(self) -> None:
        """Raise an error if the data is None."""
        if self.data is None:
            raise ValueError(
                "The data cannot be None. Please pass the data during "
                "instantiation or via the `data` attribute."
            )
