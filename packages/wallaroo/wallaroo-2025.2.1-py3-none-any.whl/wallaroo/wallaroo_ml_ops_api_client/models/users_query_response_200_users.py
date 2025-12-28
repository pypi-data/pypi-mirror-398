from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.users_query_response_200_users_additional_property_type_0 import (
        UsersQueryResponse200UsersAdditionalPropertyType0,
    )


T = TypeVar("T", bound="UsersQueryResponse200Users")


@_attrs_define
class UsersQueryResponse200Users:
    """User details keyed by User ID."""

    additional_properties: dict[
        str, Union["UsersQueryResponse200UsersAdditionalPropertyType0", None]
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.users_query_response_200_users_additional_property_type_0 import (
            UsersQueryResponse200UsersAdditionalPropertyType0,
        )

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, UsersQueryResponse200UsersAdditionalPropertyType0):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.users_query_response_200_users_additional_property_type_0 import (
            UsersQueryResponse200UsersAdditionalPropertyType0,
        )

        d = dict(src_dict)
        users_query_response_200_users = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> Union["UsersQueryResponse200UsersAdditionalPropertyType0", None]:
                if data is None:
                    return data
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    additional_property_type_0 = (
                        UsersQueryResponse200UsersAdditionalPropertyType0.from_dict(
                            data
                        )
                    )

                    return additional_property_type_0
                except:  # noqa: E722
                    pass
                return cast(
                    Union["UsersQueryResponse200UsersAdditionalPropertyType0", None],
                    data,
                )

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        users_query_response_200_users.additional_properties = additional_properties
        return users_query_response_200_users

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> Union["UsersQueryResponse200UsersAdditionalPropertyType0", None]:
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: Union["UsersQueryResponse200UsersAdditionalPropertyType0", None],
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
