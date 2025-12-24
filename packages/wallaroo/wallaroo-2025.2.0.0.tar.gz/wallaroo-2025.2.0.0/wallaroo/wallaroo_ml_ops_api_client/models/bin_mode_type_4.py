from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="BinModeType4")


@_attrs_define
class BinModeType4:
    """
    Attributes:
        provided (list[float]): A Vec of the right-edges of a set of histogram bins.
            The right-edge may be [`std::f64::INFINITY`]
    """

    provided: list[float]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provided = self.provided

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Provided": provided,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        provided = cast(list[float], d.pop("Provided"))

        bin_mode_type_4 = cls(
            provided=provided,
        )

        bin_mode_type_4.additional_properties = d
        return bin_mode_type_4

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
