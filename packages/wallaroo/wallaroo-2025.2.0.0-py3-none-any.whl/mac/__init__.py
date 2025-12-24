"""This package contains core functionality for mac.

Specifically, this package contains the following modules:
- config: configuration classes for mac components.
- entrypoints: simplified entrypoints for calling mac components.
- inference: components for serving inferences.
- io: helper functions loading custom PythonStep implementations,
    as well as data processing & validation components.
- service: components for serving a PythonStep with an exposed service.
- cli: command-line interface for serving a PythonStep.
- exceptions: custom exceptions for mac.
- types: type definitions for mac components.
"""

import logging
import os

from rich.logging import RichHandler

log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=getattr(logging, log_level, logging.DEBUG),
    handlers=[RichHandler(show_time=False)],
)

from mac.config.python_step.custom_step_config import CustomStepConfig
from mac.inference import Inference
from mac.inference.creation import InferenceBuilder
