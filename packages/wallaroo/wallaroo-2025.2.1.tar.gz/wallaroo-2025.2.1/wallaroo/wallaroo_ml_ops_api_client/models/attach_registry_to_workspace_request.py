from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="AttachRegistryToWorkspaceRequest")


@_attrs_define
class AttachRegistryToWorkspaceRequest:
    """The required information for creating a Model Registry

    Attributes:
        registry_id (UUID):
        workspace_id (int):
    """

    registry_id: UUID
    workspace_id: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        registry_id = str(self.registry_id)

        workspace_id = self.workspace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "registry_id": registry_id,
                "workspace_id": workspace_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        registry_id = UUID(d.pop("registry_id"))

        workspace_id = d.pop("workspace_id")

        attach_registry_to_workspace_request = cls(
            registry_id=registry_id,
            workspace_id=workspace_id,
        )

        attach_registry_to_workspace_request.additional_properties = d
        return attach_registry_to_workspace_request

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
