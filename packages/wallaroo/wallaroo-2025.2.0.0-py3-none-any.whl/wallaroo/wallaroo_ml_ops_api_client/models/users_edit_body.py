from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="UsersEditBody")


@_attrs_define
class UsersEditBody:
    """Edit user properties in Keycloak.

    Attributes:
        id (str):
        first_name (str):
        last_name (str):
        email (str):
        enabled (bool):  Sets the user as Active or Inactive.
        is_admin (bool):  Provides the user with the Admin role-mapping.
    """

    id: str
    first_name: str
    last_name: str
    email: str
    enabled: bool
    is_admin: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        first_name = self.first_name

        last_name = self.last_name

        email = self.email

        enabled = self.enabled

        is_admin = self.is_admin

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
                "enabled": enabled,
                "isAdmin": is_admin,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        first_name = d.pop("firstName")

        last_name = d.pop("lastName")

        email = d.pop("email")

        enabled = d.pop("enabled")

        is_admin = d.pop("isAdmin")

        users_edit_body = cls(
            id=id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            enabled=enabled,
            is_admin=is_admin,
        )

        users_edit_body.additional_properties = d
        return users_edit_body

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
