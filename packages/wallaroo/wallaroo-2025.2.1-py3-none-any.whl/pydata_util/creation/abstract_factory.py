"""This module features an implementation of the AbstractFactory pattern.
You can find more info here: https://refactoring.guru/design-patterns/abstract-factory.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from pydata_util.exceptions import SubclassTypeNotExistError

logger = logging.getLogger(__name__)


class AbstractFactory(ABC):
    """This class provides an interface for creating families of related objects
    without specifying their concrete classes.

    Attributes:
    - subclass_creators: An abstract property that holds a dictionary with keys
    corresponding to subclass names and values corresponding to the subclass creator
    functions.

    It should look like this:
    {
        "subclass_type_1": subclass / subclass creator function,
        "subclass_type_2": subclass / subclass creator function,
        ...
    }
    """

    @property
    @abstractmethod
    def subclass_creators(self) -> dict:
        """Returns a dictionary with keys corresponding to subclass names and values
        corresponding to the subclass creator functions."""

    def create(self, subclass_type: str, **kwargs) -> Any:
        """Create an instance of a concrete subclass.

        :param subclass_type: The type of the subclass to be created.
        :param kwargs: The keyword arguments to be passed to the subclass creator
        function.

        :return: An instance of a concrete subclass.
        """
        try:
            subclass_creator = self.subclass_creators[subclass_type]
        except KeyError as exception:
            message = f"The subclass type `{subclass_type}` is not supported."
            logger.exception(message)
            raise SubclassTypeNotExistError(message) from exception

        subclass = subclass_creator(**kwargs)
        return subclass
