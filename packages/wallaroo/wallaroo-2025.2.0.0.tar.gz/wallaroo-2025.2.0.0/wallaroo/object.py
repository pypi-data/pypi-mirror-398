import abc
from typing import Any, Dict, Optional, Union

import gql  # type: ignore


class DehydratedValue(object):
    """Represents a not-set sentinel value.

    Attributes that are null in the database will be returned as None in Python,
    and we want them to be set as such, so None cannot be used as a sentinel
    value signaling that an optional attribute is not yet set. Objects of this
    class fill that role instead.
    """

    def __init__(self):
        pass

    def __eq__(self, other: Any):
        """All DehydratedValue instances are equal."""
        return isinstance(other, DehydratedValue)


def rehydrate(attr):
    """Decorator that rehydrates the named attribute if needed.

    This should decorate getter calls for an attribute:

    ```
    @rehydrate(_foo_attr)
    def foo_attr(self):
        return self._foo_attr
    ```

    This will cause the API object to "rehydrate" (perform a query to fetch and
    fill in all attributes from the database) if the named attribute is not set.
    """

    def decorator(fn):
        def wrapper(*args, **kwargs):
            obj = args[0]
            present = getattr(obj, attr) != DehydratedValue()
            # Uncomment to debug while testing
            # print(
            #    "rehydrate: {} -> {}".format(
            #        attr, "present" if present else "not present"
            #    )
            # )
            if not present:
                obj._rehydrate()
            result = fn(*args, **kwargs)
            return result

        return wrapper

    return decorator


def value_if_present(data: Dict[str, Any], path: str) -> Union[Any, DehydratedValue]:
    """Returns a value in a nested dictionary, or DehydratedValue.

    :param str path: Dot-delimited path within a nested dictionary; e.g.
        `foo.bar.baz`
    :return: The requested value inside the dictionary, or DehydratedValue if it
        doesn't exist.
    """
    attrs = path.split(".")
    current = data
    for attr in attrs:
        if attr in current:
            current = current[attr]
        else:
            return DehydratedValue()
    return current


class RequiredAttributeMissing(Exception):
    """Raised when an API object is initialized without a required attribute."""

    def __init__(self, class_name: str, attribute_name: str) -> None:
        super().__init__(
            "{}: Missing required attribute '{}' in response".format(
                class_name, attribute_name
            )
        )


class ModelConversionError(Exception):
    """Raised when a model file fails to convert."""

    def __init__(self, e):
        super().__init__("Model failed to convert: {}".format(e))


class ModelConversionTimeoutError(Exception):
    """Raised when a model conversion took longer than 10mins"""

    def __init__(self, e):
        super().__init__("Model conversion did not finish: {}".format(e))


class EntityNotFoundError(Exception):
    """Raised when a query for a specific API object returns no results.

    This is specifically for queries by unique identifiers that are expected to
    return exactly one result; queries that can return 0 to many results should
    return empty list instead of raising this exception.
    """

    def __init__(self, entity_type: str, params: Dict[str, str]):
        super().__init__("{} not found: {}".format(entity_type, params))


class LimitError(Exception):
    """Raised when deployment fails."""

    def __init__(self, e):
        super().__init__(
            "You have reached a license limit in your Wallaroo instance. In order to add additional resources, you can remove some of your existing resources. If you have any questions contact us at community@wallaroo.ai: {}".format(
                e
            )
        )


class UserLimitError(Exception):
    """Raised when a community instance has hit the user limit"""

    def __init__(self):
        super().__init__(
            "You have reached the user limit in your Wallaroo instance. In order to add additional users, you can deactivate existing ones. If you have any questions contact us at community@wallaroo.ai"
        )


class DeploymentError(Exception):
    """Raised when deployment fails."""

    def __init__(self, e):
        super().__init__("Model failed to deploy: {}".format(e))


class InvalidNameError(Exception):
    """Raised when an entity's name does not meet the expected critieria.

    :param str name: the name string that is invalid
    :param str req: a string description of the requirement
    """

    def __init__(self, name: str, req: str):
        super().__init__(f"Name '{name} is invalid: {req}")


class CommunicationError(Exception):
    """Raised when some component cannot be contacted. There is a networking, configuration or
    installation problem.
    """

    def __init__(self, e):
        super().__init__("Network communication failed: {}".format(e))


class Object(abc.ABC):
    """Base class for all backend GraphQL API objects.

    This class serves as a framework for API objects to be constructed based on
    a partially-complete JSON response, and to fill in their remaining members
    dynamically if needed.
    """

    def __init__(
        self,
        gql_client: Optional[gql.Client],
        data: Dict[str, Any],
        fetch_first=False,
    ) -> None:
        """Base constructor.

        Each object requires:
        * a GraphQL client - in order to fill its missing members dynamically
        * an initial data blob - typically from unserialized JSON, contains at
        * least the data for required
          members (typically the object's primary key) and optionally other data
          members.
        """
        if gql_client is not None:
            self._gql_client = gql_client
        else:
            RuntimeError("You must use a client.")

        # Each object knows how to fill itself from the provided data.
        if fetch_first:
            self._rehydrate()
        else:
            self._fill(data)

    def _rehydrate(self):
        """Fetches all data for this object and fills in all attributes.

        Each object knows how to:
        * get data for all its attributes via the GraphQL API
        * fill in those attributes given the unserialized JSON response

        This method chains them together, so that it doesn't have to be done in
        each object.
        """
        self._fill(self._fetch_attributes())

    @abc.abstractmethod
    def _fill(self, data: Dict[str, Any]) -> None:
        """Fills an object given a response dictionary from the GraphQL API.

        Only the primary key member must be present; other members will be
        filled in via rehydration if their corresponding member function is
        called.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _fetch_attributes(self) -> Dict[str, Any]:
        """Fetches all member data from the GraphQL API."""
        raise NotImplementedError
