"""This module contains the validation errors that are used by the CLI."""


class BYOPValidationError(Exception):
    """Base exception for BYOP validation errors."""

    pass


class InferenceClassNotFoundError(BYOPValidationError):
    """Raised when no Inference-inherited class is found."""

    pass


class MultipleInferenceClassesError(BYOPValidationError):
    """Raised when multiple Inference-inherited classes are found."""

    pass


class InferenceBuilderNotFoundError(BYOPValidationError):
    """Raised when no InferenceBuilder-inherited class is found."""

    pass


class MultipleInferenceBuilderClassesError(BYOPValidationError):
    """Raised when multiple InferenceBuilder-inherited classes are found."""

    pass


class PredictMethodError(BYOPValidationError):
    """Raised when the predict method is missing or not implemented."""

    pass


class PredictMethodSignatureError(BYOPValidationError):
    """Raised when the predict method has incorrect signature."""

    pass


class ExpectedModelTypesError(BYOPValidationError):
    """Raised when the expected_model_types property is missing or not implemented."""

    pass


class InferenceMethodError(BYOPValidationError):
    """Raised when the inference method is missing or not implemented."""

    pass


class CreateMethodError(BYOPValidationError):
    """Raised when the create method is missing or not implemented."""

    pass


class ModelMethodError(BYOPValidationError):
    """Raised when the model method is missing or not implemented."""

    pass
