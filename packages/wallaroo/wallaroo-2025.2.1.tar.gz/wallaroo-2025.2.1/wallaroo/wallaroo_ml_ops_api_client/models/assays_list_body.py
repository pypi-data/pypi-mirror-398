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

T = TypeVar("T", bound="AssaysListBody")


@_attrs_define
class AssaysListBody:
    """Request for list of assays.

    Attributes:
        pipeline_id (Union[None, Unset, int]):  Optional pipeline identifier.
        workspace_id (Union[None, Unset, int]):  Optional workspace identifier.
        workspace_name (Union[None, Unset, str]):  Optional workspace name.
    """

    pipeline_id: Union[None, Unset, int] = UNSET
    workspace_id: Union[None, Unset, int] = UNSET
    workspace_name: Union[None, Unset, str] = UNSET
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

        workspace_name: Union[None, Unset, str]
        if isinstance(self.workspace_name, Unset):
            workspace_name = UNSET
        else:
            workspace_name = self.workspace_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if pipeline_id is not UNSET:
            field_dict["pipeline_id"] = pipeline_id
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id
        if workspace_name is not UNSET:
            field_dict["workspace_name"] = workspace_name

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

        def _parse_workspace_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        workspace_name = _parse_workspace_name(d.pop("workspace_name", UNSET))

        assays_list_body = cls(
            pipeline_id=pipeline_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
        )

        assays_list_body.additional_properties = d
        return assays_list_body

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
