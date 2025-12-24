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

T = TypeVar("T", bound="ListPublishesForPipelineBody")


@_attrs_define
class ListPublishesForPipelineBody:
    """Request to list published pipelines.

    Attributes:
        pipeline_id (Union[None, Unset, int]): The unique identifier for a Pipeline
        workspace_id (Union[None, Unset, int]): workspace id
    """

    pipeline_id: Union[None, Unset, int] = UNSET
    workspace_id: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pipeline_id: Union[None, Unset, int]
        if isinstance(self.pipeline_id, Unset):
            pipeline_id = UNSET
        else:
            pipeline_id = self.pipeline_id

        workspace_id: Union[None, Unset, int]
        if isinstance(self.workspace_id, Unset):
            workspace_id = UNSET
        else:
            workspace_id = self.workspace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if pipeline_id is not UNSET:
            field_dict["pipeline_id"] = pipeline_id
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_pipeline_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pipeline_id = _parse_pipeline_id(d.pop("pipeline_id", UNSET))

        def _parse_workspace_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        workspace_id = _parse_workspace_id(d.pop("workspace_id", UNSET))

        list_publishes_for_pipeline_body = cls(
            pipeline_id=pipeline_id,
            workspace_id=workspace_id,
        )

        list_publishes_for_pipeline_body.additional_properties = d
        return list_publishes_for_pipeline_body

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
