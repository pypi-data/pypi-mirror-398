"""This module contains functions to validate BYOP model structure."""

import logging
from pathlib import Path
from typing import Any, Dict, Tuple

from mac.inference import Inference
from mac.inference.creation import InferenceBuilder
from mac.validation.exceptions import (
    BYOPValidationError,
    CreateMethodError,
    ExpectedModelTypesError,
    InferenceBuilderNotFoundError,
    InferenceClassNotFoundError,
    InferenceMethodError,
    ModelMethodError,
    MultipleInferenceBuilderClassesError,
    MultipleInferenceClassesError,
    PredictMethodError,
    PredictMethodSignatureError,
)
from mac.validation.type_validation import (
    check_method_exists,
    check_property_exists,
    find_classes_derived_from,
    get_abstract_methods,
    load_python_modules_from_path,
    validate_method_signature,
)

logger = logging.getLogger(__name__)


def validate_inference_class_exists(
    modules: Dict[Path, Any],
) -> Tuple[str, type, Path]:
    """Validate that an Inference-inherited class exists.

    :param modules: Dictionary of loaded Python modules.
    :return: Tuple of (class_name, class_type, source_file).
    :raises InferenceClassNotFoundError: If no Inference class is found.
    :raises MultipleInferenceClassesError: If multiple Inference classes are found.
    """
    inference_classes = find_classes_derived_from(modules, Inference)

    if not inference_classes:
        raise InferenceClassNotFoundError(
            "No Inference-inherited class found in the model directory"
        )

    if len(inference_classes) > 1:
        class_names = [cls[0] for cls in inference_classes]
        raise MultipleInferenceClassesError(
            f"""Multiple Inference-inherited classes 
            found: {class_names}. Only one is allowed."""
        )

    return inference_classes[0]


def validate_inference_builder_class_exists(
    modules: Dict[Path, Any],
) -> Tuple[str, type, Path]:
    """Validate that an InferenceBuilder-inherited class exists.

    :param modules: Dictionary of loaded Python modules.
    :return: Tuple of (class_name, class_type, source_file).
    :raises InferenceBuilderNotFoundError: If no InferenceBuilder class is found.
    :raises MultipleInferenceBuilderClassesError: If multiple InferenceBuilder
    classes are found.
    """
    builder_classes = find_classes_derived_from(modules, InferenceBuilder)

    if not builder_classes:
        raise InferenceBuilderNotFoundError(
            "No InferenceBuilder-inherited class found in the model directory"
        )

    if len(builder_classes) > 1:
        class_names = [cls[0] for cls in builder_classes]
        raise MultipleInferenceBuilderClassesError(
            f"""Multiple InferenceBuilder-inherited classes found: {class_names}. 
            Only one is allowed."""
        )

    return builder_classes[0]


def validate_inference_builder_has_inference_method(
    builder_class: type,
) -> None:
    """Validate that the InferenceBuilder class has an inference method.

    :param builder_class: The InferenceBuilder class to validate.
    :raises InferenceMethodError: If inference method is missing or not implemented.
    """
    has_method, error = check_method_exists(
        builder_class, "inference", check_abstract=True
    )

    if not has_method:
        raise InferenceMethodError(
            "The InferenceBuilder class must contain the inference method."
        )

    has_property, _ = check_property_exists(
        builder_class, "inference", check_abstract=True
    )

    if not has_property:
        abstract_methods = get_abstract_methods(builder_class)
        if "inference" in abstract_methods:
            raise InferenceMethodError(
                "The InferenceBuilder class must contain the inference method."
            )


def validate_inference_builder_has_create_method(
    builder_class: type,
) -> None:
    """Validate that the InferenceBuilder class has a create method.

    :param builder_class: The InferenceBuilder class to validate.
    :raises CreateMethodError: If create method is missing or not implemented.
    """
    has_method, error = check_method_exists(
        builder_class, "create", check_abstract=True
    )

    if not has_method:
        raise CreateMethodError(
            "The InferenceBuilder class must contain the create method."
        )

    abstract_methods = get_abstract_methods(builder_class)
    if "create" in abstract_methods:
        raise CreateMethodError(
            "The InferenceBuilder class must contain the create method."
        )


def validate_inference_has_predict_method(
    inference_class: type,
) -> None:
    """Validate that the Inference class has a predict method.

    :param inference_class: The Inference class to validate.
    :raises PredictMethodError: If predict method is missing or
    _predict is not implemented.
    """
    has_method, error = check_method_exists(inference_class, "predict")

    if not has_method:
        raise PredictMethodError(
            f"Inference class is missing 'predict' method: {error}"
        )

    has_private_predict, _ = check_method_exists(
        inference_class, "_predict", check_abstract=True
    )

    if not has_private_predict:
        abstract_methods = get_abstract_methods(inference_class)
        if "_predict" in abstract_methods:
            raise PredictMethodError(
                "Inference class must implement the abstract '_predict' method"
            )


def validate_predict_method_signature(
    inference_class: type,
) -> None:
    """Validate that the _predict method accepts a dictionary of numpy arrays.

    :param inference_class: The Inference class to validate.
    :raises PredictMethodSignatureError: If _predict method signature is
        incorrect.
    """
    is_valid, error = validate_method_signature(
        inference_class, "_predict", {"input_data": "InferenceData"}
    )

    if not is_valid:
        raise PredictMethodSignatureError(error)


def validate_inference_has_expected_model_types(
    inference_class: type,
) -> None:
    """Validate that the Inference class has the expected_model_types property.

    :param inference_class: The Inference class to validate.
    :raises ExpectedModelTypesError: If expected_model_types
    property is missing or not implemented.
    """
    has_property, error = check_property_exists(
        inference_class, "expected_model_types", check_abstract=True
    )

    if not has_property:
        abstract_methods = get_abstract_methods(inference_class)
        if "expected_model_types" in abstract_methods:
            raise ExpectedModelTypesError(
                "Inference class must implement the abstract "
                "'expected_model_types' property"
            )
        raise ExpectedModelTypesError(
            f"Inference class is missing 'expected_model_types' property: {error}"
        )


def validate_inference_has_model_method(
    inference_class: type,
) -> None:
    """Validate that the Inference class has a model method.

    :param inference_class: The Inference class to validate.
    :raises ModelMethodError: If model method is missing or
    _model is not implemented.
    """
    has_model_in_class = "model" in inference_class.__dict__
    has_private_model_in_class = "_model" in inference_class.__dict__

    if not has_model_in_class and not has_private_model_in_class:
        raise ModelMethodError(
            "Inference class is missing the recommended model method"
        )

    has_private_model, error = check_method_exists(
        inference_class, "_model", check_abstract=True
    )

    if not has_private_model and error and "abstract" in error.lower():
        raise ModelMethodError(
            "Inference class must implement the abstract '_model' method"
        )


def validate_byop_structure(model_path: Path) -> None:
    """Validate the complete structure of a BYOP model.

    :param model_path: Path to the BYOP model directory.
    :raises FileNotFoundError: If model path doesn't exist.
    :raises BYOPValidationError: If any validation check fails.
    """
    logger.info(f"Loading Python modules from {model_path}")
    modules = load_python_modules_from_path(model_path)

    if not modules:
        raise BYOPValidationError(
            f"No Python modules found in the model directory: {model_path}"
        )

    logger.info("Checking for Inference-inherited class...")
    inference_name, inference_class, inference_file = validate_inference_class_exists(
        modules
    )
    logger.info(f"Found Inference class: {inference_name} in {inference_file}")

    logger.info("Checking for InferenceBuilder-inherited class...")
    builder_name, builder_class, builder_file = validate_inference_builder_class_exists(
        modules
    )
    logger.info(f"Found InferenceBuilder class: {builder_name} in {builder_file}")

    logger.info("Checking for inference method in InferenceBuilder class...")
    validate_inference_builder_has_inference_method(builder_class)
    logger.info("Inference method validation passed")

    logger.info("Checking for create method in InferenceBuilder class...")
    validate_inference_builder_has_create_method(builder_class)
    logger.info("Create method validation passed")

    logger.info("Checking for predict method in Inference class...")
    validate_inference_has_predict_method(inference_class)
    logger.info("Predict method validation passed")

    logger.info("Checking for model method in Inference class...")
    validate_inference_has_model_method(inference_class)
    logger.info("Model method validation passed")

    logger.info("Validating predict method signature...")
    validate_predict_method_signature(inference_class)
    logger.info("Predict method signature validation passed")

    logger.info("Checking for expected_model_types property in Inference class...")
    validate_inference_has_expected_model_types(inference_class)
    logger.info("Expected model types property validation passed")

    logger.info("BYOP model validation passed successfully")
