"""This module contains the PythonStepConfig class."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict
from pydata_util.types import SupportedFrameworks


class PythonStepConfig(BaseModel):
    """This class defines configuration parameters for a PythonStep.

    Attributes:
        - framework: The framework of the model to be loaded.
        - model_path: The path to the model.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, extra="forbid", protected_namespaces=()
    )

    framework: SupportedFrameworks
    model_path: Path
