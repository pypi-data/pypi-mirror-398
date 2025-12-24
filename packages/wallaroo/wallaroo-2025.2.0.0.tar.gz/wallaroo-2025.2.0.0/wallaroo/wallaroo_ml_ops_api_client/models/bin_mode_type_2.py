from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="BinModeType2")


@_attrs_define
class BinModeType2:
    """
    Attributes:
        quantile (int): Implementation for [BinMode::Quantile].

            This differs from [BinMode::QuantileWithExplicitOutliers] in that there are exactly N number of bins, where N is
            the number of bins requested.
            The first and last bins are [-INF, 1st Percentile) and [Last Percentile, INF)
    """

    quantile: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        quantile = self.quantile

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Quantile": quantile,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        quantile = d.pop("Quantile")

        bin_mode_type_2 = cls(
            quantile=quantile,
        )

        bin_mode_type_2.additional_properties = d
        return bin_mode_type_2

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
