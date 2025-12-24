from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteOrchestrationsBody")


@_attrs_define
class DeleteOrchestrationsBody:
    """Deletes the specified orchestrations.

    Attributes:
        orchestrations (list[UUID]): Orchestration IDs
        confirm_delete (Union[Unset, bool]): Confirm delete
    """

    orchestrations: list[UUID]
    confirm_delete: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        orchestrations = []
        for orchestrations_item_data in self.orchestrations:
            orchestrations_item = str(orchestrations_item_data)
            orchestrations.append(orchestrations_item)

        confirm_delete = self.confirm_delete

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "orchestrations": orchestrations,
            }
        )
        if confirm_delete is not UNSET:
            field_dict["confirm_delete"] = confirm_delete

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        orchestrations = []
        _orchestrations = d.pop("orchestrations")
        for orchestrations_item_data in _orchestrations:
            orchestrations_item = UUID(orchestrations_item_data)

            orchestrations.append(orchestrations_item)

        confirm_delete = d.pop("confirm_delete", UNSET)

        delete_orchestrations_body = cls(
            orchestrations=orchestrations,
            confirm_delete=confirm_delete,
        )

        delete_orchestrations_body.additional_properties = d
        return delete_orchestrations_body

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
