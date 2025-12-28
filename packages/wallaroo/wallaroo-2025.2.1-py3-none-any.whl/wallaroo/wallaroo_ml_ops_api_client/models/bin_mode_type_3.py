from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="BinModeType3")


@_attrs_define
class BinModeType3:
    """
    Attributes:
        quantile_with_explicit_outliers (int): Implementation for [BinMode::QuantileWithExplicitOutliers].

            This differs from [BinMode::Quantile] in that there are 2 more bins added after the data has been broken into
            quantiles.
            A [-INF, 0%) bin and a [100%, INF) bin.
    """

    quantile_with_explicit_outliers: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        quantile_with_explicit_outliers = self.quantile_with_explicit_outliers

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "QuantileWithExplicitOutliers": quantile_with_explicit_outliers,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        quantile_with_explicit_outliers = d.pop("QuantileWithExplicitOutliers")

        bin_mode_type_3 = cls(
            quantile_with_explicit_outliers=quantile_with_explicit_outliers,
        )

        bin_mode_type_3.additional_properties = d
        return bin_mode_type_3

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
