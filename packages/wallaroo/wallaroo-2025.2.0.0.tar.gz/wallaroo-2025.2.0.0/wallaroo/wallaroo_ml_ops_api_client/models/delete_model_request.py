from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeleteModelRequest")


@_attrs_define
class DeleteModelRequest:
    """Deletes the specified model versions.

    Attributes:
        model_id (str): Model ID
        workspace_id (int): Workspace ID
        confirm_delete (Union[Unset, bool]): Confirm delete
    """

    model_id: str
    workspace_id: int
    confirm_delete: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model_id = self.model_id

        workspace_id = self.workspace_id

        confirm_delete = self.confirm_delete

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model_id": model_id,
                "workspace_id": workspace_id,
            }
        )
        if confirm_delete is not UNSET:
            field_dict["confirm_delete"] = confirm_delete

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        model_id = d.pop("model_id")

        workspace_id = d.pop("workspace_id")

        confirm_delete = d.pop("confirm_delete", UNSET)

        delete_model_request = cls(
            model_id=model_id,
            workspace_id=workspace_id,
            confirm_delete=confirm_delete,
        )

        delete_model_request.additional_properties = d
        return delete_model_request

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
