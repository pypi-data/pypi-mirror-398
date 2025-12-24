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

T = TypeVar("T", bound="DeleteModelVersionsRequest")


@_attrs_define
class DeleteModelVersionsRequest:
    """Deletes the specified model versions.

    Attributes:
        model_versions (list[UUID]): Model version IDs
        confirm_delete (Union[Unset, bool]): Confirm delete
    """

    model_versions: list[UUID]
    confirm_delete: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model_versions = []
        for model_versions_item_data in self.model_versions:
            model_versions_item = str(model_versions_item_data)
            model_versions.append(model_versions_item)

        confirm_delete = self.confirm_delete

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model_versions": model_versions,
            }
        )
        if confirm_delete is not UNSET:
            field_dict["confirm_delete"] = confirm_delete

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        model_versions = []
        _model_versions = d.pop("model_versions")
        for model_versions_item_data in _model_versions:
            model_versions_item = UUID(model_versions_item_data)

            model_versions.append(model_versions_item)

        confirm_delete = d.pop("confirm_delete", UNSET)

        delete_model_versions_request = cls(
            model_versions=model_versions,
            confirm_delete=confirm_delete,
        )

        delete_model_versions_request.additional_properties = d
        return delete_model_versions_request

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
