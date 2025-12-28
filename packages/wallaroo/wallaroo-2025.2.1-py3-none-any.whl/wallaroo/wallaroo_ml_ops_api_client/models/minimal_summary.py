import datetime
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bins import Bins
    from ..models.series_summary_statistics import SeriesSummaryStatistics


T = TypeVar("T", bound="MinimalSummary")


@_attrs_define
class MinimalSummary:
    """A MinimalSummary is a stripped down version of the [`SeriesSummary`] that omits data that could be looked up from
    the [`crate::assays::univariate::baseline::Baseline`]

        Attributes:
            aggregated_values (list[float]): The output of aggregating data across bins.
            bins (Bins): Bins are ranges for a dataset, ranging from [`std::f64::NEG_INFINITY`] to [`std::f64::INFINITY`].
                A single bin is described by two values, the left edge (>=) and the right edge
            statistics (SeriesSummaryStatistics): Statistics that may be useful for advanced users but are not directly used
                in calculating assays.
            end (Union[None, Unset, datetime.datetime]): The end of the Baseline window used to calculate these statistics.
            start (Union[None, Unset, datetime.datetime]): The start of the Baseline window used to calculate these
                statistics.
    """

    aggregated_values: list[float]
    bins: "Bins"
    statistics: "SeriesSummaryStatistics"
    end: Union[None, Unset, datetime.datetime] = UNSET
    start: Union[None, Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        aggregated_values = self.aggregated_values

        bins = self.bins.to_dict()

        statistics = self.statistics.to_dict()

        end: Union[None, Unset, str]
        if isinstance(self.end, Unset):
            end = UNSET
        elif isinstance(self.end, datetime.datetime):
            end = self.end.isoformat()
        else:
            end = self.end

        start: Union[None, Unset, str]
        if isinstance(self.start, Unset):
            start = UNSET
        elif isinstance(self.start, datetime.datetime):
            start = self.start.isoformat()
        else:
            start = self.start

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "aggregated_values": aggregated_values,
                "bins": bins,
                "statistics": statistics,
            }
        )
        if end is not UNSET:
            field_dict["end"] = end
        if start is not UNSET:
            field_dict["start"] = start

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bins import Bins
        from ..models.series_summary_statistics import SeriesSummaryStatistics

        d = dict(src_dict)
        aggregated_values = cast(list[float], d.pop("aggregated_values"))

        bins = Bins.from_dict(d.pop("bins"))

        statistics = SeriesSummaryStatistics.from_dict(d.pop("statistics"))

        def _parse_end(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_type_0 = isoparse(data)

                return end_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        end = _parse_end(d.pop("end", UNSET))

        def _parse_start(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_type_0 = isoparse(data)

                return start_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        start = _parse_start(d.pop("start", UNSET))

        minimal_summary = cls(
            aggregated_values=aggregated_values,
            bins=bins,
            statistics=statistics,
            end=end,
            start=start,
        )

        minimal_summary.additional_properties = d
        return minimal_summary

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
