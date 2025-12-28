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
    from ..models.connections_list_response_200_connections_item import (
        ConnectionsListResponse200ConnectionsItem,
    )


T = TypeVar("T", bound="ConnectionsListResponse200")


@_attrs_define
class ConnectionsListResponse200:
    """Response from listing Connections

    Attributes:
        connections (list['ConnectionsListResponse200ConnectionsItem']):  List of Connections
    """

    connections: list["ConnectionsListResponse200ConnectionsItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        connections = []
        for connections_item_data in self.connections:
            connections_item = connections_item_data.to_dict()
            connections.append(connections_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "connections": connections,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.connections_list_response_200_connections_item import (
            ConnectionsListResponse200ConnectionsItem,
        )

        d = dict(src_dict)
        connections = []
        _connections = d.pop("connections")
        for connections_item_data in _connections:
            connections_item = ConnectionsListResponse200ConnectionsItem.from_dict(
                connections_item_data
            )

            connections.append(connections_item)

        connections_list_response_200 = cls(
            connections=connections,
        )

        connections_list_response_200.additional_properties = d
        return connections_list_response_200

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
