import datetime
from collections.abc import Mapping
from typing import (
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

from ..models.assays_get_assay_results_response_200_item_window_summary_aggregation import (
    AssaysGetAssayResultsResponse200ItemWindowSummaryAggregation,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="AssaysGetAssayResultsResponse200ItemWindowSummary")


@_attrs_define
class AssaysGetAssayResultsResponse200ItemWindowSummary:
    """Result from summarizing one sample collection.

    Attributes:
        count (int):
        min_ (float):
        max_ (float):
        mean (float):
        median (float):
        std (float):  Standard deviation.
        edges (list[float]):
        edge_names (list[str]):
        aggregated_values (list[float]):
        aggregation (AssaysGetAssayResultsResponse200ItemWindowSummaryAggregation):
        start (Union[None, Unset, datetime.datetime]):
        end (Union[None, Unset, datetime.datetime]):
    """

    count: int
    min_: float
    max_: float
    mean: float
    median: float
    std: float
    edges: list[float]
    edge_names: list[str]
    aggregated_values: list[float]
    aggregation: AssaysGetAssayResultsResponse200ItemWindowSummaryAggregation
    start: Union[None, Unset, datetime.datetime] = UNSET
    end: Union[None, Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        count = self.count

        min_ = self.min_

        max_ = self.max_

        mean = self.mean

        median = self.median

        std = self.std

        edges = self.edges

        edge_names = self.edge_names

        aggregated_values = self.aggregated_values

        aggregation = self.aggregation.value

        start: Union[None, Unset, str]
        if isinstance(self.start, Unset):
            start = UNSET
        elif isinstance(self.start, datetime.datetime):
            start = self.start.isoformat()
        else:
            start = self.start

        end: Union[None, Unset, str]
        if isinstance(self.end, Unset):
            end = UNSET
        elif isinstance(self.end, datetime.datetime):
            end = self.end.isoformat()
        else:
            end = self.end

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "count": count,
                "min": min_,
                "max": max_,
                "mean": mean,
                "median": median,
                "std": std,
                "edges": edges,
                "edge_names": edge_names,
                "aggregated_values": aggregated_values,
                "aggregation": aggregation,
            }
        )
        if start is not UNSET:
            field_dict["start"] = start
        if end is not UNSET:
            field_dict["end"] = end

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        count = d.pop("count")

        min_ = d.pop("min")

        max_ = d.pop("max")

        mean = d.pop("mean")

        median = d.pop("median")

        std = d.pop("std")

        edges = cast(list[float], d.pop("edges"))

        edge_names = cast(list[str], d.pop("edge_names"))

        aggregated_values = cast(list[float], d.pop("aggregated_values"))

        aggregation = AssaysGetAssayResultsResponse200ItemWindowSummaryAggregation(
            d.pop("aggregation")
        )

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

        assays_get_assay_results_response_200_item_window_summary = cls(
            count=count,
            min_=min_,
            max_=max_,
            mean=mean,
            median=median,
            std=std,
            edges=edges,
            edge_names=edge_names,
            aggregated_values=aggregated_values,
            aggregation=aggregation,
            start=start,
            end=end,
        )

        assays_get_assay_results_response_200_item_window_summary.additional_properties = d
        return assays_get_assay_results_response_200_item_window_summary

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
