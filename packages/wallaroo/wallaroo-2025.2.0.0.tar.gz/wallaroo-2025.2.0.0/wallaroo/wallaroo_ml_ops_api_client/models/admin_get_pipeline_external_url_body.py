from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="AdminGetPipelineExternalUrlBody")


@_attrs_define
class AdminGetPipelineExternalUrlBody:
    """Request for pipeline URL-related operations.

    Attributes:
        workspace_id (int):  Unique workspace identifier.
        pipeline_name (str):  Name of the pipeline.
    """

    workspace_id: int
    pipeline_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workspace_id = self.workspace_id

        pipeline_name = self.pipeline_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workspace_id": workspace_id,
                "pipeline_name": pipeline_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        workspace_id = d.pop("workspace_id")

        pipeline_name = d.pop("pipeline_name")

        admin_get_pipeline_external_url_body = cls(
            workspace_id=workspace_id,
            pipeline_name=pipeline_name,
        )

        admin_get_pipeline_external_url_body.additional_properties = d
        return admin_get_pipeline_external_url_body

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
