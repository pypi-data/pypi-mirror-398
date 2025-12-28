from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkspacesListUsersResponse200UsersItem")


@_attrs_define
class WorkspacesListUsersResponse200UsersItem:
    """User data returned as part of the List Workspace Users call

    Attributes:
        user_id (str):  User UUID identifier
        user_type (Union[None, Unset, str]):  User type, Collaborator or Owner
    """

    user_id: str
    user_type: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        user_type: Union[None, Unset, str]
        if isinstance(self.user_type, Unset):
            user_type = UNSET
        else:
            user_type = self.user_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
            }
        )
        if user_type is not UNSET:
            field_dict["user_type"] = user_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("user_id")

        def _parse_user_type(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_type = _parse_user_type(d.pop("user_type", UNSET))

        workspaces_list_users_response_200_users_item = cls(
            user_id=user_id,
            user_type=user_type,
        )

        workspaces_list_users_response_200_users_item.additional_properties = d
        return workspaces_list_users_response_200_users_item

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
