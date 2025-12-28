"""This module contains helper functions for type checking and validation utilities."""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type

logger = logging.getLogger(__name__)


def load_python_modules_from_path(model_path: Path) -> Dict[Path, Any]:
    """Load all Python modules from the given path.

    :param model_path: Path to the directory containing Python files.
    :return: Dictionary mapping file paths to loaded modules.
    """
    modules = {}

    if not model_path.exists():
        raise FileNotFoundError(f"Model path does not exist: {model_path}")

    python_files = list(model_path.glob("**/*.py"))

    for py_file in python_files:
        try:
            if "__pycache__" in str(py_file):
                continue

            module_name = py_file.stem
            spec = importlib.util.spec_from_file_location(module_name, py_file)

            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                modules[py_file] = module
                logger.debug(f"Successfully loaded module from {py_file}")
        except Exception as e:
            logger.warning(f"Failed to load module from {py_file}: {e}")

    return modules


def find_classes_derived_from(
    modules: Dict[Path, Any], base_class: Type, exclude_base: bool = True
) -> List[Tuple[str, Type, Path]]:
    """Find all classes that inherit from the given base class.

    Only finds classes actually defined in the provided modules,
    not imported classes.

    :param modules: Dictionary of loaded modules.
    :param base_class: The base class to check inheritance from.
    :param exclude_base: Whether to exclude the base class itself.
    :return: List of tuples containing (class_name, class_type, source_file).
    """
    derived_classes = []
    seen_classes = set()

    for file_path, module in modules.items():
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, base_class):
                continue

            if exclude_base and obj is base_class:
                continue

            # Only include classes defined in this module, not imported ones
            try:
                # Check if the class was defined in this module by comparing
                # the module name. For dynamically loaded modules,
                # inspect.getmodule() might return None, so we check __module__
                if obj.__module__ != module.__name__:
                    continue
            except Exception:
                continue

            # Check for duplicates and avoid them
            if obj in seen_classes:
                continue

            seen_classes.add(obj)
            derived_classes.append((name, obj, file_path))

    return derived_classes


def check_method_exists(
    class_type: Type, method_name: str, check_abstract: bool = False
) -> Tuple[bool, Optional[str]]:
    """Check if a method exists in a class.

    :param class_type: The class to check.
    :param method_name: The name of the method to look for.
    :param check_abstract: Whether to check if the method is abstract.
    :return: Tuple of (exists, error_message).
    """
    try:
        if hasattr(class_type, method_name):
            method = getattr(class_type, method_name)

            if check_abstract:
                if (
                    hasattr(method, "__isabstractmethod__")
                    and method.__isabstractmethod__
                ):
                    return (
                        False,
                        f"Method '{method_name}' is abstract and not implemented",
                    )

            return True, None
        else:
            return (
                False,
                f"Method '{method_name}' not found in class {class_type.__name__}",
            )

    except Exception as e:
        return False, f"Error checking method '{method_name}': {str(e)}"


def check_property_exists(
    class_type: Type, property_name: str, check_abstract: bool = False
) -> Tuple[bool, Optional[str]]:
    """Check if a property exists in a class.

    :param class_type: The class to check.
    :param property_name: The name of the property to look for.
    :param check_abstract: Whether to check if the property is abstract.
    :return: Tuple of (exists, error_message).
    """
    try:
        if hasattr(class_type, property_name):
            prop = getattr(class_type, property_name)

            if isinstance(prop, property):
                if check_abstract:
                    if (
                        prop.fget is not None
                        and hasattr(prop.fget, "__isabstractmethod__")
                        and prop.fget.__isabstractmethod__
                    ):
                        return (
                            False,
                            f"""Property '{property_name}' is abstract 
                            and not implemented""",
                        )

                return True, None
            else:
                return True, None
        else:
            return (
                False,
                f"Property '{property_name}' not found in class {class_type.__name__}",
            )

    except Exception as e:
        return False, f"Error checking property '{property_name}': {str(e)}"


def get_abstract_methods(class_type: Type) -> Set[str]:
    """Get all abstract methods that are not implemented in a class.

    :param class_type: The class to check.
    :return: Set of abstract method names.
    """
    abstract_methods = set()

    for name, value in inspect.getmembers(class_type):
        if getattr(value, "__isabstractmethod__", False):
            abstract_methods.add(name)

    return abstract_methods


def _is_dictionary_of_numpy_arrays(type_annotation: Any) -> Tuple[bool, Optional[str]]:
    """Helper function to check if a type annotation represents a
        dictionary of numpy arrays.

    :param type_annotation: The type annotation to check.
    :return: Tuple of (is_valid, error_message).
    """
    from typing import get_args, get_origin

    origin = get_origin(type_annotation)

    if origin not in (dict, Dict):
        return False, "type must be a dictionary"

    args = get_args(type_annotation)
    if args:
        value_type_str = str(args[1]) if len(args) > 1 else str(args[0])
        has_ndarray = "ndarray" in value_type_str.lower() or "NDArray" in value_type_str

        if not has_ndarray:
            return False, "dictionary values must be numpy arrays"

    return True, None


def _get_method_signature(
    class_type: Type, method_name: str
) -> Tuple[Any, Any, Optional[str]]:
    """Helper function to get method and signature with error handling.

    :param class_type: The class to get method from.
    :param method_name: The name of the method.
    :return: Tuple of (method, signature, error_message).
    """
    try:
        method = getattr(class_type, method_name)
        sig = inspect.signature(method)
        return method, sig, None
    except Exception as e:
        return None, None, f"Error getting method '{method_name}': {str(e)}"


def validate_method_signature(
    class_type: Type, method_name: str, expected_param_types: Dict[str, str]
) -> Tuple[bool, Optional[str]]:
    """Validate that predict method accepts a dictionary of numpy arrays.

    :param class_type: The class to validate.
    :param method_name: The name of the method to validate.
    :param expected_param_types: Dictionary mapping parameter names to expected types.
    :raises TypeError: If the method signature is incorrect.
    """
    method, sig, error = _get_method_signature(class_type, method_name)
    if error:
        return False, error

    if "input_data" not in sig.parameters:
        return False, f"'{method_name}' method must have an 'input_data' parameter"

    param = sig.parameters["input_data"]

    if param.annotation == inspect.Parameter.empty:
        return (
            False,
            f"'{method_name}' method's 'input_data' parameter "
            "is missing type annotation",
        )

    is_valid, error_msg = _is_dictionary_of_numpy_arrays(param.annotation)
    if not is_valid:
        return (
            False,
            "The Inference class's predict method may only accept a "
            "dictionary of numpy arrays.",
        )

    return True, None


def validate_method_return_type(
    class_type: Type, method_name: str
) -> Tuple[bool, Optional[str]]:
    """Validate that predict method returns a dictionary of numpy arrays.

    :param class_type: The class to validate.
    :param method_name: The name of the method to validate.
    :return: Tuple of (is_valid, error_message).
    """
    method, sig, error = _get_method_signature(class_type, method_name)
    if error:
        return False, error

    # Check if method has a return annotation
    if sig.return_annotation == inspect.Signature.empty:
        return (
            False,
            f"'{method_name}' method is missing return type annotation",
        )

    is_valid, error_msg = _is_dictionary_of_numpy_arrays(sig.return_annotation)
    if not is_valid:
        return (
            False,
            "The Inference class's predict method may only return a "
            "dictionary of numpy arrays.",
        )

    return True, None
