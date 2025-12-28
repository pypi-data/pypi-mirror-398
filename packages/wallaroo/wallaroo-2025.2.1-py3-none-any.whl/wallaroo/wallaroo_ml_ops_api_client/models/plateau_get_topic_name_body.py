from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="PlateauGetTopicNameBody")


@_attrs_define
class PlateauGetTopicNameBody:
    """Request for topic name.

    Attributes:
        workspace_id (Union[None, Unset, int]):  Workspace identifier.
        pipeline_name (Union[None, Unset, str]):  Pipeline name.
        pipeline_pk_id (Union[None, Unset, int]):  Internal pipeline identifier.
    """

    workspace_id: Union[None, Unset, int] = UNSET
    pipeline_name: Union[None, Unset, str] = UNSET
    pipeline_pk_id: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        workspace_id: Union[None, Unset, int]
        if isinstance(self.workspace_id, Unset):
            workspace_id = UNSET
        else:
            workspace_id = self.workspace_id

        pipeline_name: Union[None, Unset, str]
        if isinstance(self.pipeline_name, Unset):
            pipeline_name = UNSET
        else:
            pipeline_name = self.pipeline_name

        pipeline_pk_id: Union[None, Unset, int]
        if isinstance(self.pipeline_pk_id, Unset):
            pipeline_pk_id = UNSET
        else:
            pipeline_pk_id = self.pipeline_pk_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id
        if pipeline_name is not UNSET:
            field_dict["pipeline_name"] = pipeline_name
        if pipeline_pk_id is not UNSET:
            field_dict["pipeline_pk_id"] = pipeline_pk_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_workspace_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        workspace_id = _parse_workspace_id(d.pop("workspace_id", UNSET))

        def _parse_pipeline_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        pipeline_name = _parse_pipeline_name(d.pop("pipeline_name", UNSET))

        def _parse_pipeline_pk_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pipeline_pk_id = _parse_pipeline_pk_id(d.pop("pipeline_pk_id", UNSET))

        plateau_get_topic_name_body = cls(
            workspace_id=workspace_id,
            pipeline_name=pipeline_name,
            pipeline_pk_id=pipeline_pk_id,
        )

        plateau_get_topic_name_body.additional_properties = d
        return plateau_get_topic_name_body

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
