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

from ..models.assays_list_response_200_item_summarizer_type_0_aggregation import (
    AssaysListResponse200ItemSummarizerType0Aggregation,
)
from ..models.assays_list_response_200_item_summarizer_type_0_bin_mode import (
    AssaysListResponse200ItemSummarizerType0BinMode,
)
from ..models.assays_list_response_200_item_summarizer_type_0_metric import (
    AssaysListResponse200ItemSummarizerType0Metric,
)
from ..models.assays_list_response_200_item_summarizer_type_0_type import (
    AssaysListResponse200ItemSummarizerType0Type,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="AssaysListResponse200ItemSummarizerType0")


@_attrs_define
class AssaysListResponse200ItemSummarizerType0:
    """Defines the summarizer/test we want to conduct

    Attributes:
        bin_mode (AssaysListResponse200ItemSummarizerType0BinMode):
        aggregation (AssaysListResponse200ItemSummarizerType0Aggregation):
        metric (AssaysListResponse200ItemSummarizerType0Metric):  How we calculate the score between two
            histograms/vecs.  Add pct_diff and sum_pct_diff?
        num_bins (int):
        type_ (AssaysListResponse200ItemSummarizerType0Type):
        bin_weights (Union[None, Unset, list[float]]):
        provided_edges (Union[None, Unset, list[float]]):
    """

    bin_mode: AssaysListResponse200ItemSummarizerType0BinMode
    aggregation: AssaysListResponse200ItemSummarizerType0Aggregation
    metric: AssaysListResponse200ItemSummarizerType0Metric
    num_bins: int
    type_: AssaysListResponse200ItemSummarizerType0Type
    bin_weights: Union[None, Unset, list[float]] = UNSET
    provided_edges: Union[None, Unset, list[float]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bin_mode = self.bin_mode.value

        aggregation = self.aggregation.value

        metric = self.metric.value

        num_bins = self.num_bins

        type_ = self.type_.value

        bin_weights: Union[None, Unset, list[float]]
        if isinstance(self.bin_weights, Unset):
            bin_weights = UNSET
        elif isinstance(self.bin_weights, list):
            bin_weights = self.bin_weights

        else:
            bin_weights = self.bin_weights

        provided_edges: Union[None, Unset, list[float]]
        if isinstance(self.provided_edges, Unset):
            provided_edges = UNSET
        elif isinstance(self.provided_edges, list):
            provided_edges = self.provided_edges

        else:
            provided_edges = self.provided_edges

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "bin_mode": bin_mode,
                "aggregation": aggregation,
                "metric": metric,
                "num_bins": num_bins,
                "type": type_,
            }
        )
        if bin_weights is not UNSET:
            field_dict["bin_weights"] = bin_weights
        if provided_edges is not UNSET:
            field_dict["provided_edges"] = provided_edges

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        bin_mode = AssaysListResponse200ItemSummarizerType0BinMode(d.pop("bin_mode"))

        aggregation = AssaysListResponse200ItemSummarizerType0Aggregation(
            d.pop("aggregation")
        )

        metric = AssaysListResponse200ItemSummarizerType0Metric(d.pop("metric"))

        num_bins = d.pop("num_bins")

        type_ = AssaysListResponse200ItemSummarizerType0Type(d.pop("type"))

        def _parse_bin_weights(data: object) -> Union[None, Unset, list[float]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                bin_weights_type_0 = cast(list[float], data)

                return bin_weights_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[float]], data)

        bin_weights = _parse_bin_weights(d.pop("bin_weights", UNSET))

        def _parse_provided_edges(data: object) -> Union[None, Unset, list[float]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                provided_edges_type_0 = cast(list[float], data)

                return provided_edges_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[float]], data)

        provided_edges = _parse_provided_edges(d.pop("provided_edges", UNSET))

        assays_list_response_200_item_summarizer_type_0 = cls(
            bin_mode=bin_mode,
            aggregation=aggregation,
            metric=metric,
            num_bins=num_bins,
            type_=type_,
            bin_weights=bin_weights,
            provided_edges=provided_edges,
        )

        assays_list_response_200_item_summarizer_type_0.additional_properties = d
        return assays_list_response_200_item_summarizer_type_0

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
