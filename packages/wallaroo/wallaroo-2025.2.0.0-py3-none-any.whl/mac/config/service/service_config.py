"""This module contains the ServiceConfig class.
ServiceConfig is the base class for all service-related configurations.
"""

from abc import abstractmethod

from pydantic_settings import BaseSettings, SettingsConfigDict

from mac.config.python_step import PythonStepConfig
from mac.config.service.server_config import ServerConfig
from mac.types import SupportedServices


class ServiceConfig(BaseSettings):
    """This class represents the configuration for a Service object."""

    model_config = SettingsConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
    )

    python_step: PythonStepConfig
    server: ServerConfig = ServerConfig()

    @property
    @abstractmethod
    def service_type(self) -> SupportedServices:
        """This property specifies the type of service this configuration is for."""
