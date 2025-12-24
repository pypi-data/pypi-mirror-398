"""This module features the ArrowFlightServiceConfig class."""

import logging

import pyarrow as pa
from pydantic import Field

from mac.config.service.service_config import ServiceConfig
from mac.types import SupportedServices

logger = logging.getLogger(__name__)


class ArrowFlightServiceConfig(ServiceConfig):
    """This class represents the configuration of an ArrowFlightService."""

    output_schema: pa.Schema = Field(
        description="The output schema of the `PythonStep`",
    )
    use_lock: bool = Field(
        default=True,
        description="Whether to use a lock to synchronize access to `PythonStep`",
    )
    max_queue_depth: int = Field(
        default=128,
        ge=1,
        description="The maximum queue depth when using the asynchronous server",
    )
    request_timeout: None | float = Field(
        default=None,
        description="The request timeout when using the asynchronous server",
    )

    @property
    def service_type(self) -> SupportedServices:
        """This property specifies the type of service this configuration is for."""
        return SupportedServices.FLIGHT
