# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = wallaroo_api_endpoint_default_error_from_dict(json.loads(json_string))

from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class WallarooAPIEndpointDefaultError:
    """The catch all error for telemetry responses."""

    """A detailed error message."""
    message: str

    def __init__(self, message: str) -> None:
        self.message = message

    @staticmethod
    def from_dict(obj: Any) -> "WallarooAPIEndpointDefaultError":
        assert isinstance(obj, dict)
        message = from_str(obj.get("message"))
        return WallarooAPIEndpointDefaultError(message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["message"] = from_str(self.message)
        return result


def wallaroo_api_endpoint_default_error_from_dict(
    s: Any,
) -> WallarooAPIEndpointDefaultError:
    return WallarooAPIEndpointDefaultError.from_dict(s)


def wallaroo_api_endpoint_default_error_to_dict(
    x: WallarooAPIEndpointDefaultError,
) -> Any:
    return to_class(WallarooAPIEndpointDefaultError, x)
