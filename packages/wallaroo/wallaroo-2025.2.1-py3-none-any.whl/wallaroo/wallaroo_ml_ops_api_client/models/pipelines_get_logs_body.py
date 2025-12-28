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

from ..models.pipelines_get_logs_body_order import PipelinesGetLogsBodyOrder
from ..types import UNSET, Unset

T = TypeVar("T", bound="PipelinesGetLogsBody")


@_attrs_define
class PipelinesGetLogsBody:
    """Request to retrieve inference logs for a pipeline.

    Attributes:
        pipeline_name (str):  Pipeline identifier.
        workspace_id (int):  Workspace identifier.
        order (PipelinesGetLogsBodyOrder):  Iteration order
        cursor (Union[None, Unset, str]):  Cursor returned with a previous page of results
        page_size (Union[None, Unset, int]):  Max records per page
        start_time (Union[None, Unset, str]):  RFC 3339 start time
        end_time (Union[None, Unset, str]):  RFC 3339 end time
    """

    pipeline_name: str
    workspace_id: int
    order: PipelinesGetLogsBodyOrder
    cursor: Union[None, Unset, str] = UNSET
    page_size: Union[None, Unset, int] = UNSET
    start_time: Union[None, Unset, str] = UNSET
    end_time: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pipeline_name = self.pipeline_name

        workspace_id = self.workspace_id

        order = self.order.value

        cursor: Union[None, Unset, str]
        if isinstance(self.cursor, Unset):
            cursor = UNSET
        else:
            cursor = self.cursor

        page_size: Union[None, Unset, int]
        if isinstance(self.page_size, Unset):
            page_size = UNSET
        else:
            page_size = self.page_size

        start_time: Union[None, Unset, str]
        if isinstance(self.start_time, Unset):
            start_time = UNSET
        else:
            start_time = self.start_time

        end_time: Union[None, Unset, str]
        if isinstance(self.end_time, Unset):
            end_time = UNSET
        else:
            end_time = self.end_time

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pipeline_name": pipeline_name,
                "workspace_id": workspace_id,
                "order": order,
            }
        )
        if cursor is not UNSET:
            field_dict["cursor"] = cursor
        if page_size is not UNSET:
            field_dict["page_size"] = page_size
        if start_time is not UNSET:
            field_dict["start_time"] = start_time
        if end_time is not UNSET:
            field_dict["end_time"] = end_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        pipeline_name = d.pop("pipeline_name")

        workspace_id = d.pop("workspace_id")

        order = PipelinesGetLogsBodyOrder(d.pop("order"))

        def _parse_cursor(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        cursor = _parse_cursor(d.pop("cursor", UNSET))

        def _parse_page_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        page_size = _parse_page_size(d.pop("page_size", UNSET))

        def _parse_start_time(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        start_time = _parse_start_time(d.pop("start_time", UNSET))

        def _parse_end_time(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        end_time = _parse_end_time(d.pop("end_time", UNSET))

        pipelines_get_logs_body = cls(
            pipeline_name=pipeline_name,
            workspace_id=workspace_id,
            order=order,
            cursor=cursor,
            page_size=page_size,
            start_time=start_time,
            end_time=end_time,
        )

        pipelines_get_logs_body.additional_properties = d
        return pipelines_get_logs_body

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
