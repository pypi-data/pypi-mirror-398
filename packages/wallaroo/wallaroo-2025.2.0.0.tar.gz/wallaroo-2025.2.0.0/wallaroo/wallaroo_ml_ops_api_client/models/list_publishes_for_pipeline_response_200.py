from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.edge import Edge
    from ..models.pipeline_publish import PipelinePublish


T = TypeVar("T", bound="ListPublishesForPipelineResponse200")


@_attrs_define
class ListPublishesForPipelineResponse200:
    """Response with a list of published pipelines.

    Attributes:
        edges (list['Edge']): list of edges for the pipeline
        publishes (list['PipelinePublish']): list of published pipelines
    """

    edges: list["Edge"]
    publishes: list["PipelinePublish"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        edges = []
        for edges_item_data in self.edges:
            edges_item = edges_item_data.to_dict()
            edges.append(edges_item)

        publishes = []
        for publishes_item_data in self.publishes:
            publishes_item = publishes_item_data.to_dict()
            publishes.append(publishes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "edges": edges,
                "publishes": publishes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.edge import Edge
        from ..models.pipeline_publish import PipelinePublish

        d = dict(src_dict)
        edges = []
        _edges = d.pop("edges")
        for edges_item_data in _edges:
            edges_item = Edge.from_dict(edges_item_data)

            edges.append(edges_item)

        publishes = []
        _publishes = d.pop("publishes")
        for publishes_item_data in _publishes:
            publishes_item = PipelinePublish.from_dict(publishes_item_data)

            publishes.append(publishes_item)

        list_publishes_for_pipeline_response_200 = cls(
            edges=edges,
            publishes=publishes,
        )

        list_publishes_for_pipeline_response_200.additional_properties = d
        return list_publishes_for_pipeline_response_200

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
