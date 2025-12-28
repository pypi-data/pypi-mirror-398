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
    from ..models.workspaces_list_users_response_200_users_item import (
        WorkspacesListUsersResponse200UsersItem,
    )


T = TypeVar("T", bound="WorkspacesListUsersResponse200")


@_attrs_define
class WorkspacesListUsersResponse200:
    """Response for a successful List Workspace Users call.

    Attributes:
        users (list['WorkspacesListUsersResponse200UsersItem']):  Users belonging to the specified workspace.
    """

    users: list["WorkspacesListUsersResponse200UsersItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        users = []
        for users_item_data in self.users:
            users_item = users_item_data.to_dict()
            users.append(users_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "users": users,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.workspaces_list_users_response_200_users_item import (
            WorkspacesListUsersResponse200UsersItem,
        )

        d = dict(src_dict)
        users = []
        _users = d.pop("users")
        for users_item_data in _users:
            users_item = WorkspacesListUsersResponse200UsersItem.from_dict(
                users_item_data
            )

            users.append(users_item)

        workspaces_list_users_response_200 = cls(
            users=users,
        )

        workspaces_list_users_response_200.additional_properties = d
        return workspaces_list_users_response_200

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
