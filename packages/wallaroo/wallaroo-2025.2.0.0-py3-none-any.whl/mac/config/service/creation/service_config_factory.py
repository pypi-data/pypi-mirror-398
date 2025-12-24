"""This module features the ServiceConfigFactory for creating
concrete ServiceConfig subclass instances."""

from pydata_util.creation import AbstractFactory

from mac.config.service import (
    ArrowFlightServiceConfig,
    MLflowServiceConfig,
)
from mac.types import SupportedServices

subclass_creators = {
    SupportedServices.MLFLOW.value: MLflowServiceConfig,  # type: ignore[dict-item]
    SupportedServices.FLIGHT.value: ArrowFlightServiceConfig,
}


class ServiceConfigFactory(AbstractFactory):
    """This class implements the AbstractFactory interface
    for creating concrete ServiceConfig subclass instances."""

    @property
    def subclass_creators(self) -> dict:
        """Returns a dictionary of supported inference services and
        their corresponding subclass creators.

        :return: A dictionary of subclass creators.
        """
        return subclass_creators
