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


T = TypeVar("T", bound="ListPipelineVersionsResponse200")


@_attrs_define
class ListPipelineVersionsResponse200:
    """Response with a list of published pipelines.

    Attributes:
        pipeline_versions (list['ListPipelineItem']): list of pipelines
    """

    pipeline_versions: list["ListPipelineItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pipeline_versions = []
        for pipeline_versions_item_data in self.pipeline_versions:
            pipeline_versions_item = pipeline_versions_item_data.to_dict()
            pipeline_versions.append(pipeline_versions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pipeline_versions": pipeline_versions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.list_pipeline_item import ListPipelineItem

        d = dict(src_dict)
        pipeline_versions = []
        _pipeline_versions = d.pop("pipeline_versions")
        for pipeline_versions_item_data in _pipeline_versions:
            pipeline_versions_item = ListPipelineItem.from_dict(
                pipeline_versions_item_data
            )

            pipeline_versions.append(pipeline_versions_item)

        list_pipeline_versions_response_200 = cls(
            pipeline_versions=pipeline_versions,
        )

        list_pipeline_versions_response_200.additional_properties = d
        return list_pipeline_versions_response_200

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
