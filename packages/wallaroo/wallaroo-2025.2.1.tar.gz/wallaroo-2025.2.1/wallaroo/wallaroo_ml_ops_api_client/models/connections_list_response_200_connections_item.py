import datetime
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
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.connections_list_response_200_connections_item_details_type_0 import (
        ConnectionsListResponse200ConnectionsItemDetailsType0,
    )


T = TypeVar("T", bound="ConnectionsListResponse200ConnectionsItem")


@_attrs_define
class ConnectionsListResponse200ConnectionsItem:
    """Info for a connection

    Attributes:
        id (str):
        name (str):
        type_ (str):
        created_at (datetime.datetime):
        workspace_names (list[str]):
        details (Union['ConnectionsListResponse200ConnectionsItemDetailsType0', None, Unset]):
    """

    id: str
    name: str
    type_: str
    created_at: datetime.datetime
    workspace_names: list[str]
    details: Union[
        "ConnectionsListResponse200ConnectionsItemDetailsType0", None, Unset
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.connections_list_response_200_connections_item_details_type_0 import (
            ConnectionsListResponse200ConnectionsItemDetailsType0,
        )

        id = self.id

        name = self.name

        type_ = self.type_

        created_at = self.created_at.isoformat()

        workspace_names = self.workspace_names

        details: Union[None, Unset, dict[str, Any]]
        if isinstance(self.details, Unset):
            details = UNSET
        elif isinstance(
            self.details, ConnectionsListResponse200ConnectionsItemDetailsType0
        ):
            details = self.details.to_dict()
        else:
            details = self.details

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "type": type_,
                "created_at": created_at,
                "workspace_names": workspace_names,
            }
        )
        if details is not UNSET:
            field_dict["details"] = details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.connections_list_response_200_connections_item_details_type_0 import (
            ConnectionsListResponse200ConnectionsItemDetailsType0,
        )

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        type_ = d.pop("type")

        created_at = isoparse(d.pop("created_at"))

        workspace_names = cast(list[str], d.pop("workspace_names"))

        def _parse_details(
            data: object,
        ) -> Union[
            "ConnectionsListResponse200ConnectionsItemDetailsType0", None, Unset
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                details_type_0 = (
                    ConnectionsListResponse200ConnectionsItemDetailsType0.from_dict(
                        data
                    )
                )

                return details_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "ConnectionsListResponse200ConnectionsItemDetailsType0", None, Unset
                ],
                data,
            )

        details = _parse_details(d.pop("details", UNSET))

        connections_list_response_200_connections_item = cls(
            id=id,
            name=name,
            type_=type_,
            created_at=created_at,
            workspace_names=workspace_names,
            details=details,
        )

        connections_list_response_200_connections_item.additional_properties = d
        return connections_list_response_200_connections_item

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
