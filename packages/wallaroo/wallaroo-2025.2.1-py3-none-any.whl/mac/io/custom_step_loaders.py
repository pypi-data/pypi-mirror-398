"""This module features helper functions for loading a custom PythonStep."""

import importlib
import inspect
import logging
from functools import partial
from pathlib import Path
from typing import Any, Callable, List, Tuple, Type

from pydata_util.nats.framework_config import CustomConfig

from mac.config.python_step import CustomStepConfig
from mac.inference.creation.inference_builder import InferenceBuilder
from mac.types import InferenceData, PythonStep

logger = logging.getLogger(__name__)

ImportedCls = Tuple[str, Type]
ImportedFunc = Tuple[str, Callable]


def is_class_member(obj: Callable) -> bool:
    """Checks if the given object is a class member.

    :param obj: The object to check.

    :return: True if the given object is a class member, False otherwise.
    """
    return inspect.isclass(obj)


def is_function(obj: Callable) -> bool:
    """Checks if the given object is a function.

    :param obj: The object to check.

    :return: True if the given object is a class member, False otherwise.
    """
    return inspect.isfunction(obj)


def is_object_derived_from_class(imported_cls: ImportedCls, obj_type: Type) -> bool:
    """Checks if the imported class is derived from the given object type.

    :param imported_cls: The imported class to check.
    :param obj_type: The object type.

    :return: True if the given object is derived from the given class, False otherwise.
    """
    cls_name, cls = imported_cls
    return issubclass(cls, obj_type) and cls_name != obj_type.__name__


def is_process_data_func(imported_func: ImportedFunc) -> bool:
    """Checks if the given object is a `process_data` function
    with the correct signature.

    :param imported_func: The name and instance of an
    imported function.

    :raises ValueError: If the `process_data` function signature is incorrect.

    :return: True if the given object is a `process_data` function.
    """
    func_name, func = imported_func
    expected_func_def = "async def" if inspect.iscoroutinefunction(func) else "def"

    signature = inspect.signature(func)
    input_args = list(signature.parameters.items())
    is_signature_correct = (
        len(input_args) == 1
        and input_args[0][0] == "input_data"
        and input_args[0][1].annotation == InferenceData
        and signature.return_annotation == InferenceData
    )

    match (func_name, is_signature_correct):
        case ("process_data", False):
            message = (
                "The `process_data` function should have the following signature: "
                f"{expected_func_def} process_data(input_data: InferenceData) -> "
                "InferenceData:`."
            )
            logger.error(message)
            raise ValueError(message)
        case ("process_data", True):
            return True
        case _:
            return False


def import_py_module_from_path(file_path: Path, spec_name: str) -> Any:
    """Import a python module from a given file path.

    :param file_path: The path of the file to import the module from.
    :param spec_name: The name to import the module as.

    :return: The imported module.
    """
    spec = importlib.util.spec_from_file_location(spec_name, file_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore

    try:
        spec.loader.exec_module(module)  # type: ignore
    except FileNotFoundError as exc:
        message = f"Could not load module from file: {file_path.as_posix()}."
        logger.error(message, exc_info=True)
        raise exc

    return module


def load_custom_inference(
    custom_step_config: CustomStepConfig,
    custom_config: CustomConfig,
) -> PythonStep:
    """Load custom inference from the python modules specified in a
    given custom step config.

    :param custom_step_config: The custom step config that contains
    configuration for loading the custom step.
    :param custom_config: The custom config included in the NATS message.

    :return: An custom PythonStep that relates to a custom Inference.
    """
    logger.info("Loading custom Inference step from Python files...")

    custom_inference_builders: List[ImportedCls] = list(
        filter(
            partial(is_object_derived_from_class, obj_type=InferenceBuilder),  # type: ignore[arg-type]
            [
                imported_cls
                for py_file in custom_step_config.matching_files  # type: ignore[union-attr]
                for imported_cls in inspect.getmembers(
                    import_py_module_from_path(py_file, "custom_inference"),
                    is_class_member,
                )
            ],
        )
    )

    if len(custom_inference_builders) > 1:
        message = message = (
            "Multiple InferenceBuilder subclasses found in the given files."  # noqa: E501
        )
        logger.error(message)
        raise ValueError(message)

    if not custom_inference_builders:
        message = "No InferenceBuilder subclass found in the given files."
        logger.error(message)
        raise AttributeError(message)

    logger.info("Loading successful.")

    _, custom_inference_builder = custom_inference_builders[0]
    custom_inference_builder.custom_config = custom_config
    custom_inference = custom_inference_builder().create(custom_step_config)

    return custom_inference.predict


def load_custom_step(
    custom_step_config: CustomStepConfig,
) -> PythonStep:
    """Load custom step from the python modules specified in a
    given custom step config.

    :param custom_step_config: The custom step config that contains
    configuration for loading the custom step.

    :return: An custom PythonStep.
    """
    logger.info("Loading custom pre/post-processing step from Python files...")

    custom_steps: List[ImportedFunc] = list(
        filter(
            is_process_data_func,  # type: ignore[arg-type]
            [
                imported_func
                for py_file in custom_step_config.matching_files  # type: ignore[union-attr]
                for imported_func in inspect.getmembers(
                    import_py_module_from_path(py_file, "custom_step"), is_function
                )
            ],
        )
    )

    if len(custom_steps) > 1:
        message = "Multiple pre/post-processing steps found in the given files."
        logger.error(message)
        raise ValueError(message)

    if not custom_steps:
        message = "No pre/post-processing step found in the given files."
        logger.error(message)
        raise AttributeError(message)

    logger.info("Loading successful.")

    _, custom_step = custom_steps[0]

    return custom_step
