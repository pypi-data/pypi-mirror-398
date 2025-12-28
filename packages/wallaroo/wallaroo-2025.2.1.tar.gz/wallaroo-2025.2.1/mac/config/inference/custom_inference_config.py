"""This module contains the CustomInferenceConfig class.
This class defines configuration parameters for a custom Inference object.

NOTE: `CustomInferenceConfig` is deprecated internally and replaced
by `PythonStepConfig`, but is left as is since it's still used
on the SDK for type annotations.
"""

import logging
from pathlib import Path
from typing import Optional, Set

from pydantic import model_validator
from pydata_util.types import SupportedFrameworks

from mac.config.python_step import PythonStepConfig

logger = logging.getLogger(__name__)


class CustomInferenceConfig(PythonStepConfig):
    """This class defines configuration parameters for a custom Inference object."""

    # Python modules to include
    matching_files: Optional[Set[Path]] = None
    modules_to_include: Set[Path]

    @model_validator(mode="before")
    @classmethod
    def raise_error_if_framework_invalid(cls, data):
        """Checks that the framework is supported."""
        if data["framework"] != SupportedFrameworks.CUSTOM:
            message = "`framework` should be of type `SupportedFrameworks.CUSTOM`."
            logger.error(message)
            raise ValueError(message)
        return data

    @model_validator(mode="before")
    @classmethod
    def raise_error_if_model_path_not_dir(cls, data):
        """Checks that the model_path is a directory.
        model_path should be a folder containing custom Python modules,
        model files and (optionally) pip requirements."""
        if not data["model_path"].is_dir():
            message = "`model_path` should be a directory."
            logger.error(message)
            raise ValueError(message)
        return data

    @model_validator(mode="after")  # type: ignore
    @classmethod
    def raise_error_if_modules_not_py_files(cls, model_instance):
        """Checks that all the module files are .py files."""
        model_instance.matching_files = set(
            [
                file
                for path in model_instance.modules_to_include
                for file in list(
                    model_instance.model_path.glob(path.as_posix())
                )  # modules are always included in the model_path
            ]
        )

        if not model_instance.matching_files:
            message = "No matching files found inside `model_path`."
            logger.error(message)
            raise FileNotFoundError(message)

        if any(file.suffix != ".py" for file in model_instance.matching_files):
            message = "`modules_to_include` must only match .py files."
            logger.error(message)
            raise ValueError(message)

        return model_instance
