from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
)
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="DeletePipelineVersionsBody")


@_attrs_define
class DeletePipelineVersionsBody:
    """Request to list published pipelines.

    Attributes:
        pipeline_versions (list[UUID]): Pipeline ID
    """

    pipeline_versions: list[UUID]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pipeline_versions = []
        for pipeline_versions_item_data in self.pipeline_versions:
            pipeline_versions_item = str(pipeline_versions_item_data)
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
        d = dict(src_dict)
        pipeline_versions = []
        _pipeline_versions = d.pop("pipeline_versions")
        for pipeline_versions_item_data in _pipeline_versions:
            pipeline_versions_item = UUID(pipeline_versions_item_data)

            pipeline_versions.append(pipeline_versions_item)

        delete_pipeline_versions_body = cls(
            pipeline_versions=pipeline_versions,
        )

        delete_pipeline_versions_body.additional_properties = d
        return delete_pipeline_versions_body

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
