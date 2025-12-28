from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="OldPublish")


@_attrs_define
class OldPublish:
    """
    Attributes:
        id (int):
        pipeline_name (str):
        pipeline_version_name (UUID):
    """

    id: int
    pipeline_name: str
    pipeline_version_name: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        pipeline_name = self.pipeline_name

        pipeline_version_name = str(self.pipeline_version_name)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "pipeline_name": pipeline_name,
                "pipeline_version_name": pipeline_version_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        pipeline_name = d.pop("pipeline_name")

        pipeline_version_name = UUID(d.pop("pipeline_version_name"))

        old_publish = cls(
            id=id,
            pipeline_name=pipeline_name,
            pipeline_version_name=pipeline_version_name,
        )

        old_publish.additional_properties = d
        return old_publish

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
