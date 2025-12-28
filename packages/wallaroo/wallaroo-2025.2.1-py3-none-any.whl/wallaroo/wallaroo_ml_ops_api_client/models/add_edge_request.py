from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="AddEdgeRequest")


@_attrs_define
class AddEdgeRequest:
    """Request to publish a pipeline.

    Attributes:
        name (str):
        pipeline_publish_id (int):
        tags (list[str]):
    """

    name: str
    pipeline_publish_id: int
    tags: list[str]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        pipeline_publish_id = self.pipeline_publish_id

        tags = self.tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "pipeline_publish_id": pipeline_publish_id,
                "tags": tags,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        pipeline_publish_id = d.pop("pipeline_publish_id")

        tags = cast(list[str], d.pop("tags"))

        add_edge_request = cls(
            name=name,
            pipeline_publish_id=pipeline_publish_id,
            tags=tags,
        )

        add_edge_request.additional_properties = d
        return add_edge_request

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
