# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = wallaroo_api_get_tlscertv1_from_dict(json.loads(json_string))

from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class WallarooAPIGetTLSCERTV1:
    """Result from requesting the most recent TLS cert"""

    """Text of the latest certificate"""
    tls_certificate: str
    """Text of the latest private key"""
    tls_key: str

    def __init__(self, tls_certificate: str, tls_key: str) -> None:
        self.tls_certificate = tls_certificate
        self.tls_key = tls_key

    @staticmethod
    def from_dict(obj: Any) -> "WallarooAPIGetTLSCERTV1":
        assert isinstance(obj, dict)
        tls_certificate = from_str(obj.get("tls_certificate"))
        tls_key = from_str(obj.get("tls_key"))
        return WallarooAPIGetTLSCERTV1(tls_certificate, tls_key)

    def to_dict(self) -> dict:
        result: dict = {}
        result["tls_certificate"] = from_str(self.tls_certificate)
        result["tls_key"] = from_str(self.tls_key)
        return result


def wallaroo_api_get_tlscertv1_from_dict(s: Any) -> WallarooAPIGetTLSCERTV1:
    return WallarooAPIGetTLSCERTV1.from_dict(s)


def wallaroo_api_get_tlscertv1_to_dict(x: WallarooAPIGetTLSCERTV1) -> Any:
    return to_class(WallarooAPIGetTLSCERTV1, x)
