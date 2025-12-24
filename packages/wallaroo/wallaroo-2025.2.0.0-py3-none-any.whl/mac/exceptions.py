"""This module defines custom exceptions for the mac package."""

import logging

logger = logging.getLogger(__name__)


class ArrowΤοΝDArrayConversionError(Exception):
    """This exception is raised if converting `pa.Array`
    to `InferenceData` is raising an error."""

    def __init__(self, message: str) -> None:
        """Initializes the ArrowΤοΝDArrayConversionError class.

        :param message: The message of the exception.
        """
        super().__init__(message)


class FlightSchemaNotImplementedError(NotImplementedError):
    """This exception is raised if the `get_schema` RPC is not implemented in
    Arrow Flight RPC."""

    def __init__(self, message: str) -> None:
        """Initializes the FlightSchemaNotImplementedError class.

        :param message: The message of the exception.
        """
        super().__init__(message)


class InferenceDataValidationError(Exception):
    """This exception is raised if the InferenceData is not valid."""

    def __init__(self, message: str) -> None:
        """Initializes the InferenceDataValidationError class.

        :param message: The message of the exception.
        """
        super().__init__(message)


class InferencePostprocessingError(Exception):
    """This exception is raised if the Postprocessor.postprocess() raises an error."""

    def __init__(self, message: str) -> None:
        """Initializes the InferencePostprocessingError class.

        :param message: The message of the exception.
        """
        super().__init__(message)


class InferencePreprocessingError(Exception):
    """This exception is raised if the Preprocessor.preprocess() raises an error."""

    def __init__(self, message: str) -> None:
        """Initializes the InferencePreprocessingError class.

        :param message: The message of the exception.
        """
        super().__init__(message)


class InferenceTypeError(Exception):
    """This exception is raised if the Inference doesn't have the correct type."""

    def __init__(self, message: str) -> None:
        """Initializes the InferenceTypeError class.

        :param message: The message of the exception.
        """
        super().__init__(message)


class MLflowModelSignatureError(Exception):
    """This exception is raised if the ModelSignature is not in the right format
    for MLflow."""

    def __init__(self, message: str) -> None:
        """Initializes the MLflowModelSignatureError class.

        :param message: The message of the exception.
        """
        super().__init__(message)


class ModelNotAssignedError(Exception):
    """This exception is raised if the model is not assigned to the inference."""

    def __init__(self, message: str) -> None:
        """Initializes the ModelNotAssignedError class.

        :param message: The message of the exception.
        """
        super().__init__(message)


class PythonStepError(Exception):
    """This exception is raised if running the `PythonStep`
    raises an error."""

    def __init__(self, message: str) -> None:
        """Initializes the PythonStepError class.

        :param message: The message of the exception.
        """
        super().__init__(message)


class NDArrayToArrowConversionError(Exception):
    """This exception is raised if converting `InferenceData`
    to `pa.Array` is raising an error."""

    def __init__(self, message: str) -> None:
        """Initializes the NDArrayToArrowConversionError class.

        :param message: The message of the exception.
        """
        super().__init__(message)


class PandasRecordsConversionError(Exception):
    """This exception is raised if converting InferenceData to/from pandas records
    is raising an error."""

    def __init__(self, message: str) -> None:
        """Initializes the PandasRecordsConversionError class.

        :param message: The message of the exception.
        """
        super().__init__(message)
