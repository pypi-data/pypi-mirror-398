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
    from ..models.list_pipeline_item import ListPipelineItem


T = TypeVar("T", bound="ListPipelinesResponse200")


@_attrs_define
class ListPipelinesResponse200:
    """Response with a list of published pipelines.

    Attributes:
        pipelines (list['ListPipelineItem']): list of pipelines
    """

    pipelines: list["ListPipelineItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pipelines = []
        for pipelines_item_data in self.pipelines:
            pipelines_item = pipelines_item_data.to_dict()
            pipelines.append(pipelines_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pipelines": pipelines,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.list_pipeline_item import ListPipelineItem

        d = dict(src_dict)
        pipelines = []
        _pipelines = d.pop("pipelines")
        for pipelines_item_data in _pipelines:
            pipelines_item = ListPipelineItem.from_dict(pipelines_item_data)

            pipelines.append(pipelines_item)

        list_pipelines_response_200 = cls(
            pipelines=pipelines,
        )

        list_pipelines_response_200.additional_properties = d
        return list_pipelines_response_200

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
