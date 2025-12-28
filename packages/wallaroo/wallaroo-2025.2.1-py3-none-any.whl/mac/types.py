"""This module defines custom types for the mac package."""

from enum import Enum
from typing import Awaitable, Callable, Dict

import numpy.typing as npt
from typing_extensions import TypeAlias

# PythonStep related types
InferenceData: TypeAlias = Dict[str, npt.NDArray]
PythonStep: TypeAlias = Callable[[InferenceData], InferenceData]
AsyncPythonStep: TypeAlias = Callable[[InferenceData], Awaitable[InferenceData]]


class SupportedServices(str, Enum):
    """This class defines an Enum for supported services that
    can be used to serve a `PythonStep` for inference purposes.
    """

    MLFLOW = "mlflow"
    FLIGHT = "flight"
