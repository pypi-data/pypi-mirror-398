from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.task_status import TaskStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.list_all_orchestrations_request_time_range_type_0_item import (
        ListAllOrchestrationsRequestTimeRangeType0Item,
    )


T = TypeVar("T", bound="ListAllOrchestrationsRequest")


@_attrs_define
class ListAllOrchestrationsRequest:
    """
    Attributes:
        task_run_status (list[TaskStatus]):
        workspace_ids (list[int]):
        killed (Union[None, Unset, bool]):
        time_range (Union[None, Unset, list['ListAllOrchestrationsRequestTimeRangeType0Item']]):
    """

    task_run_status: list[TaskStatus]
    workspace_ids: list[int]
    killed: Union[None, Unset, bool] = UNSET
    time_range: Union[
        None, Unset, list["ListAllOrchestrationsRequestTimeRangeType0Item"]
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        task_run_status = []
        for task_run_status_item_data in self.task_run_status:
            task_run_status_item = task_run_status_item_data.value
            task_run_status.append(task_run_status_item)

        workspace_ids = self.workspace_ids

        killed: Union[None, Unset, bool]
        if isinstance(self.killed, Unset):
            killed = UNSET
        else:
            killed = self.killed

        time_range: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.time_range, Unset):
            time_range = UNSET
        elif isinstance(self.time_range, list):
            time_range = []
            for time_range_type_0_item_data in self.time_range:
                time_range_type_0_item = time_range_type_0_item_data.to_dict()
                time_range.append(time_range_type_0_item)

        else:
            time_range = self.time_range

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "task_run_status": task_run_status,
                "workspace_ids": workspace_ids,
            }
        )
        if killed is not UNSET:
            field_dict["killed"] = killed
        if time_range is not UNSET:
            field_dict["time_range"] = time_range

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.list_all_orchestrations_request_time_range_type_0_item import (
            ListAllOrchestrationsRequestTimeRangeType0Item,
        )

        d = dict(src_dict)
        task_run_status = []
        _task_run_status = d.pop("task_run_status")
        for task_run_status_item_data in _task_run_status:
            task_run_status_item = TaskStatus(task_run_status_item_data)

            task_run_status.append(task_run_status_item)

        workspace_ids = cast(list[int], d.pop("workspace_ids"))

        def _parse_killed(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        killed = _parse_killed(d.pop("killed", UNSET))

        def _parse_time_range(
            data: object,
        ) -> Union[None, Unset, list["ListAllOrchestrationsRequestTimeRangeType0Item"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                time_range_type_0 = []
                _time_range_type_0 = data
                for time_range_type_0_item_data in _time_range_type_0:
                    time_range_type_0_item = (
                        ListAllOrchestrationsRequestTimeRangeType0Item.from_dict(
                            time_range_type_0_item_data
                        )
                    )

                    time_range_type_0.append(time_range_type_0_item)

                return time_range_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    None, Unset, list["ListAllOrchestrationsRequestTimeRangeType0Item"]
                ],
                data,
            )

        time_range = _parse_time_range(d.pop("time_range", UNSET))

        list_all_orchestrations_request = cls(
            task_run_status=task_run_status,
            workspace_ids=workspace_ids,
            killed=killed,
            time_range=time_range,
        )

        list_all_orchestrations_request.additional_properties = d
        return list_all_orchestrations_request

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
