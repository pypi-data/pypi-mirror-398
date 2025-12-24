"""This module features the MLflowServiceConfig class."""

import logging
from typing import Dict

from mac.config.service import ServiceConfig
from mac.types import SupportedServices

logger = logging.getLogger(__name__)


class MLflowServiceConfig(ServiceConfig):
    """This class represents the configuration of MLflowService."""

    model_signature: None | Dict[str, str] = None

    @property
    def service_type(self) -> SupportedServices:
        """This property specifies the type of service this configuration is for."""
        return SupportedServices.MLFLOW
