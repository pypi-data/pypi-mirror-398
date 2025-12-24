from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="BinModeType1")


@_attrs_define
class BinModeType1:
    """
    Attributes:
        equal (int): Implementation for [BinMode::Equal].

            Currently, Equal bins calculations implicitly assume that the first and last bins will capture all outliers.
            We could split this behavior out as we do in [BinMode::Quantile] and [BinMode::QuantileWithExplicitOutliers],
            or make a configuration option that selectively includes or excludes outliers from the first/last bins.
    """

    equal: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        equal = self.equal

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Equal": equal,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        equal = d.pop("Equal")

        bin_mode_type_1 = cls(
            equal=equal,
        )

        bin_mode_type_1.additional_properties = d
        return bin_mode_type_1

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
