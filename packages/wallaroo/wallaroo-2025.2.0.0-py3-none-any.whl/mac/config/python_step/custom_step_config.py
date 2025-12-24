"""This module contains the CustomStepConfig class."""

import logging
from pathlib import Path
from typing import Optional, Set

from pydantic import DirectoryPath, model_validator
from pydata_util.types import SupportedFrameworks

from mac.config.python_step.python_step_config import PythonStepConfig

logger = logging.getLogger(__name__)

available_frameworks = (
    SupportedFrameworks.CUSTOM,
    SupportedFrameworks.PYTHON,
)


class CustomStepConfig(PythonStepConfig):
    """This class defines configuration parameters for a custom PythonStep,
    that can either be a pre/post-processing or an Inference step.

    Attributes:
        - framework: The framework of the model to be loaded, that should match
            `available_frameworks`.
        - model_path: The path to the model.
        - matching_files: The files that match the `modules_to_include` pattern.
        - modules_to_include: The patterns to match the files to include in the model.
            It can be either a list of Path objects pointing to actual files or a
            regex pattern (e.g. `*.py` to include all .py files in the model_path).
    """

    model_path: DirectoryPath
    matching_files: Optional[Set[Path]] = None
    modules_to_include: Set[Path]

    @model_validator(mode="before")
    @classmethod
    def raise_error_if_framework_invalid(cls, data):
        """Checks that the framework is supported."""
        if data["framework"] not in available_frameworks:
            message = f"`framework` should be one of `{available_frameworks}`."
            logger.error(message)
            raise ValueError(message)
        return data

    @model_validator(mode="after")  # type: ignore
    @classmethod
    def raise_error_if_modules_not_py_files(cls, self):
        """Checks that all the module files are .py files."""
        self.matching_files = set(
            [
                file
                for path in self.modules_to_include
                for file in list(
                    self.model_path.glob(path.as_posix())
                )  # modules are always included in the model_path
            ]
        )

        if not self.matching_files:
            message = "No matching files found inside `model_path`."
            logger.error(message)
            raise FileNotFoundError(message)

        if any(file.suffix != ".py" for file in self.matching_files):
            message = "`modules_to_include` must only match .py files."
            logger.error(message)
            raise ValueError(message)

        return self
