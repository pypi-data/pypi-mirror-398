from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="RemoveRegistryFromWorkspaceResponse200")


@_attrs_define
class RemoveRegistryFromWorkspaceResponse200:
    """
    Attributes:
        id (UUID): The unique identifier for the Model Registry
        workspace_id (int): The unique identifier for the workspace.
    """

    id: UUID
    workspace_id: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        workspace_id = self.workspace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "workspace_id": workspace_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        workspace_id = d.pop("workspace_id")

        remove_registry_from_workspace_response_200 = cls(
            id=id,
            workspace_id=workspace_id,
        )

        remove_registry_from_workspace_response_200.additional_properties = d
        return remove_registry_from_workspace_response_200

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
