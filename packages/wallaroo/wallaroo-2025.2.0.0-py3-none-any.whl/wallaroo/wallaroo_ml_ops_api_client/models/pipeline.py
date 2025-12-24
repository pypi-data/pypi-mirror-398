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

T = TypeVar("T", bound="Pipeline")


@_attrs_define
class Pipeline:
    """Definition of an inference pipeline that can be deployed on the edge.

    Attributes:
        created_at (datetime.datetime): When this [Pipeline] was created.
            Optional because they are read-only
        id (int): The unique identifier of a [Pipeline].
        name (str):
        updated_at (datetime.datetime): When this [Pipeline] was last updated.
            Optional because they are read-only
    """

    created_at: datetime.datetime
    id: int
    name: str
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        id = self.id

        name = self.name

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "created_at": created_at,
                "id": id,
                "name": name,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        id = d.pop("id")

        name = d.pop("name")

        updated_at = isoparse(d.pop("updated_at"))

        pipeline = cls(
            created_at=created_at,
            id=id,
            name=name,
            updated_at=updated_at,
        )

        pipeline.additional_properties = d
        return pipeline

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
