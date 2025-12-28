from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="DeletePipelineResponse200")


@_attrs_define
class DeletePipelineResponse200:
    """
    Attributes:
        pipeline_id (str): Pipeline ID
        workspace_id (int): Workspace ID
    """

    pipeline_id: str
    workspace_id: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pipeline_id = self.pipeline_id

        workspace_id = self.workspace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pipeline_id": pipeline_id,
                "workspace_id": workspace_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        pipeline_id = d.pop("pipeline_id")

        workspace_id = d.pop("workspace_id")

        delete_pipeline_response_200 = cls(
            pipeline_id=pipeline_id,
            workspace_id=workspace_id,
        )

        delete_pipeline_response_200.additional_properties = d
        return delete_pipeline_response_200

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
