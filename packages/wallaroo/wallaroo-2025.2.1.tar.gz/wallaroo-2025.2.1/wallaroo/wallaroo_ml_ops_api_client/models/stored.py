import datetime
from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

T = TypeVar("T", bound="Stored")


@_attrs_define
class Stored:
    """
    Attributes:
        stored (list[datetime.datetime]): Use data from the time range specified as the Window.
    """

    stored: list[datetime.datetime]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        stored = []
        for stored_item_data in self.stored:
            stored_item = stored_item_data.isoformat()
            stored.append(stored_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Stored": stored,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        stored = []
        _stored = d.pop("Stored")
        for stored_item_data in _stored:
            stored_item = isoparse(stored_item_data)

            stored.append(stored_item)

        stored = cls(
            stored=stored,
        )

        stored.additional_properties = d
        return stored

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
