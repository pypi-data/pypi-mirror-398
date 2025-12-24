"""This module features the StreamlinedDLInference class, that extends
the StreamlinedInference interface, and can be used to run end-to-end inference
on a wrapped Inference subclass.
"""

# pylint: disable=protected-access
import logging
from typing import Any

from mac.inference.inference import Inference
from mac.inference.streamlined_inference import StreamlinedInference
from mac.io.data_processing import BasePreprocessor, Postprocessor
from mac.io.data_validation import DataValidator
from mac.types import InferenceData

logger = logging.getLogger(__name__)


class StreamlinedDLInference(StreamlinedInference):
    """This class extends the StreamlinedInference interface, and can be used
    to run a basic streamlined inference on for arbitrary frameworks.

    Attributes:
        - expected_model_types: A set of model instance types that are expected
            by this inference.
        - wrappee: The Inference subclass that is wrapped by this
            StreamlinedDLInference.
        - data_validator: An DataValidator instance that is used to validate the input
            data.
        - preprocessor: A BasePreprocessor instance that is used to preprocess
            the input data.
        - postprocessor: A Postprocessor instance that is used to postprocess
            the output data.
    """

    def __init__(
        self,
        wrappee: Inference,
        preprocessor: BasePreprocessor,
        postprocessor: Postprocessor,
        data_validator: DataValidator,
    ) -> None:
        super().__init__(wrappee, preprocessor, postprocessor, data_validator)

    def _preprocess(self, data: InferenceData) -> Any:
        """Preprocess the input data if data is multi-output."""
        if self._data_validator.expected_keys:  # type: ignore [union-attr, attr-defined] # noqa: E501
            self._preprocessor.expected_keys = (  # type: ignore [union-attr, attr-defined] # noqa: E501
                self._data_validator.expected_keys  # type: ignore [union-attr, attr-defined] # noqa: E501
            )
        return self._preprocessor.preprocess(data=data)
