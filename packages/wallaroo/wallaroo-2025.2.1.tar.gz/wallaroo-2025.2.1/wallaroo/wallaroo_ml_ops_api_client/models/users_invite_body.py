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

T = TypeVar("T", bound="UsersInviteBody")


@_attrs_define
class UsersInviteBody:
    """Invitation request for a new user.

    Attributes:
        email (str):  New user's email address.
        roles (list[str]):
        password (Union[None, Unset, str]):  Optional initial password to send.
        require_reset (Union[None, Unset, bool]):
    """

    email: str
    roles: list[str]
    password: Union[None, Unset, str] = UNSET
    require_reset: Union[None, Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        roles = self.roles

        password: Union[None, Unset, str]
        if isinstance(self.password, Unset):
            password = UNSET
        else:
            password = self.password

        require_reset: Union[None, Unset, bool]
        if isinstance(self.require_reset, Unset):
            require_reset = UNSET
        else:
            require_reset = self.require_reset

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
                "roles": roles,
            }
        )
        if password is not UNSET:
            field_dict["password"] = password
        if require_reset is not UNSET:
            field_dict["require_reset"] = require_reset

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        roles = cast(list[str], d.pop("roles"))

        def _parse_password(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        password = _parse_password(d.pop("password", UNSET))

        def _parse_require_reset(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        require_reset = _parse_require_reset(d.pop("require_reset", UNSET))

        users_invite_body = cls(
            email=email,
            roles=roles,
            password=password,
            require_reset=require_reset,
        )

        users_invite_body.additional_properties = d
        return users_invite_body

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
