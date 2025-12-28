"""This module features the NATSMessageFactory for creating
concrete NATSMessage subclass instances."""

import logging

from pydata_util.creation.abstract_factory import AbstractFactory
from pydata_util.nats.nats_message import NATSConversionMessage, NATSPackagingMessage
from pydata_util.types import SupportedNATSMessages

logger = logging.getLogger(__name__)


class NATSMessageFactory(AbstractFactory):
    """This class implements the AbstractFactory interface
    for creating concrete NATSMessage subclass instances."""

    @property
    def subclass_creators(self) -> dict:
        """Returns a dictionary with keys corresponding to subclass names and values
        corresponding to the subclass creator functions."""
        return {
            SupportedNATSMessages.CONVERSION: NATSConversionMessage,
            SupportedNATSMessages.PACKAGING: NATSPackagingMessage,
        }
