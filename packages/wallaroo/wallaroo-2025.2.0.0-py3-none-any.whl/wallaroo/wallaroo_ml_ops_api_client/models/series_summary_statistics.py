from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="SeriesSummaryStatistics")


@_attrs_define
class SeriesSummaryStatistics:
    """Statistics that may be useful for advanced users but are not directly used in calculating assays.

    Attributes:
        count (int):
        max_ (float):
        mean (float):
        median (float):
        min_ (float):
        std (float): Standard deviation.
    """

    count: int
    max_: float
    mean: float
    median: float
    min_: float
    std: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        max_ = self.max_

        mean = self.mean

        median = self.median

        min_ = self.min_

        std = self.std

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "count": count,
                "max": max_,
                "mean": mean,
                "median": median,
                "min": min_,
                "std": std,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        count = d.pop("count")

        max_ = d.pop("max")

        mean = d.pop("mean")

        median = d.pop("median")

        min_ = d.pop("min")

        std = d.pop("std")

        series_summary_statistics = cls(
            count=count,
            max_=max_,
            mean=mean,
            median=median,
            min_=min_,
            std=std,
        )

        series_summary_statistics.additional_properties = d
        return series_summary_statistics

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
