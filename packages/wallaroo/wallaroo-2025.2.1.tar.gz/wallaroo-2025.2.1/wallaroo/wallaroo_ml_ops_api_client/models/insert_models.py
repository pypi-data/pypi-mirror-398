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
    from ..models.models import Models


T = TypeVar("T", bound="InsertModels")


@_attrs_define
class InsertModels:
    """
    Attributes:
        returning (list['Models']):
    """

    returning: list["Models"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        returning = []
        for returning_item_data in self.returning:
            returning_item = returning_item_data.to_dict()
            returning.append(returning_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "returning": returning,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.models import Models

        d = dict(src_dict)
        returning = []
        _returning = d.pop("returning")
        for returning_item_data in _returning:
            returning_item = Models.from_dict(returning_item_data)

            returning.append(returning_item)

        insert_models = cls(
            returning=returning,
        )

        insert_models.additional_properties = d
        return insert_models

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
