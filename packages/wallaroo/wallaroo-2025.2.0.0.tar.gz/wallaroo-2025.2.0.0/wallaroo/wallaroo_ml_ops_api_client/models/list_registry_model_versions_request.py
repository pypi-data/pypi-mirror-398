from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="ListRegistryModelVersionsRequest")


@_attrs_define
class ListRegistryModelVersionsRequest:
    """Payload for the List Registry Models call.

    Attributes:
        model_name (str):
        registry_id (UUID):
    """

    model_name: str
    registry_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model_name = self.model_name

        registry_id = str(self.registry_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model_name": model_name,
                "registry_id": registry_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        model_name = d.pop("model_name")

        registry_id = UUID(d.pop("registry_id"))

        list_registry_model_versions_request = cls(
            model_name=model_name,
            registry_id=registry_id,
        )

        list_registry_model_versions_request.additional_properties = d
        return list_registry_model_versions_request

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
