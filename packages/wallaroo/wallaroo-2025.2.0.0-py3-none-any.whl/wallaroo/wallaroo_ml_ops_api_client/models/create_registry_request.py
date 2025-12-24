from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="CreateRegistryRequest")


@_attrs_define
class CreateRegistryRequest:
    """The required information for creating a Model Registry

    Attributes:
        name (str): See [ModelRegistry]
        token (str): A user t
        url (str):
        workspace_id (int):
    """

    name: str
    token: str
    url: str
    workspace_id: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        token = self.token

        url = self.url

        workspace_id = self.workspace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "token": token,
                "url": url,
                "workspace_id": workspace_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        token = d.pop("token")

        url = d.pop("url")

        workspace_id = d.pop("workspace_id")

        create_registry_request = cls(
            name=name,
            token=token,
            url=url,
            workspace_id=workspace_id,
        )

        create_registry_request.additional_properties = d
        return create_registry_request

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
