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

T = TypeVar("T", bound="GetPublishStatusBody")


@_attrs_define
class GetPublishStatusBody:
    """Request to fetch a pipeline publish status.

    Attributes:
        id (int): The ID of the pipeline publish
        include_replace_bundles (Union[Unset, bool]): Whether to include the bundles for the edges this pipeline publish
            is a replacement for
    """

    id: int
    include_replace_bundles: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        include_replace_bundles = self.include_replace_bundles

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if include_replace_bundles is not UNSET:
            field_dict["include_replace_bundles"] = include_replace_bundles

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        include_replace_bundles = d.pop("include_replace_bundles", UNSET)

        get_publish_status_body = cls(
            id=id,
            include_replace_bundles=include_replace_bundles,
        )

        get_publish_status_body.additional_properties = d
        return get_publish_status_body

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
