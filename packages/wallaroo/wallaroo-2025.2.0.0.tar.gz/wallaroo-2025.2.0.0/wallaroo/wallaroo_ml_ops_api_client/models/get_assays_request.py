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

from ..models.filter_on_active import FilterOnActive
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetAssaysRequest")


@_attrs_define
class GetAssaysRequest:
    """
    Attributes:
        active (FilterOnActive):
        pipeline_name (Union[None, Unset, str]):
        workspace_id (Union[None, Unset, int]): Workspace ID
    """

    active: FilterOnActive
    pipeline_name: Union[None, Unset, str] = UNSET
    workspace_id: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        active = self.active.value

        pipeline_name: Union[None, Unset, str]
        if isinstance(self.pipeline_name, Unset):
            pipeline_name = UNSET
        else:
            pipeline_name = self.pipeline_name

        workspace_id: Union[None, Unset, int]
        if isinstance(self.workspace_id, Unset):
            workspace_id = UNSET
        else:
            workspace_id = self.workspace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "active": active,
            }
        )
        if pipeline_name is not UNSET:
            field_dict["pipeline_name"] = pipeline_name
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        active = FilterOnActive(d.pop("active"))

        def _parse_pipeline_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        pipeline_name = _parse_pipeline_name(d.pop("pipeline_name", UNSET))

        def _parse_workspace_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        workspace_id = _parse_workspace_id(d.pop("workspace_id", UNSET))

        get_assays_request = cls(
            active=active,
            pipeline_name=pipeline_name,
            workspace_id=workspace_id,
        )

        get_assays_request.additional_properties = d
        return get_assays_request

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
