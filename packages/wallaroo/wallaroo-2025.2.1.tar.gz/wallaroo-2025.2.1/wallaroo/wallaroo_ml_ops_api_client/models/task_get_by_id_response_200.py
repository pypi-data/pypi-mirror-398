import datetime
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.arbex_status import ArbexStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.task_get_by_id_response_200_input_data import (
        TaskGetByIdResponse200InputData,
    )
    from ..models.task_run import TaskRun


T = TypeVar("T", bound="TaskGetByIdResponse200")


@_attrs_define
class TaskGetByIdResponse200:
    """
    Attributes:
        created_at (datetime.datetime):
        id (UUID):
        input_data (TaskGetByIdResponse200InputData):
        killed (bool):
        last_runs (list['TaskRun']): A list of the (by default: 5) most recent runs associated with this Task.
            This will only ever be more than 1 in the case of the Scheduled/Cron run.
        status (ArbexStatus):
        updated_at (datetime.datetime):
        workspace_id (int):
        name (Union[None, Unset, str]):
    """

    created_at: datetime.datetime
    id: UUID
    input_data: "TaskGetByIdResponse200InputData"
    killed: bool
    last_runs: list["TaskRun"]
    status: ArbexStatus
    updated_at: datetime.datetime
    workspace_id: int
    name: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        id = str(self.id)

        input_data = self.input_data.to_dict()

        killed = self.killed

        last_runs = []
        for last_runs_item_data in self.last_runs:
            last_runs_item = last_runs_item_data.to_dict()
            last_runs.append(last_runs_item)

        status = self.status.value

        updated_at = self.updated_at.isoformat()

        workspace_id = self.workspace_id

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "created_at": created_at,
                "id": id,
                "input_data": input_data,
                "killed": killed,
                "last_runs": last_runs,
                "status": status,
                "updated_at": updated_at,
                "workspace_id": workspace_id,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_get_by_id_response_200_input_data import (
            TaskGetByIdResponse200InputData,
        )
        from ..models.task_run import TaskRun

        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        id = UUID(d.pop("id"))

        input_data = TaskGetByIdResponse200InputData.from_dict(d.pop("input_data"))

        killed = d.pop("killed")

        last_runs = []
        _last_runs = d.pop("last_runs")
        for last_runs_item_data in _last_runs:
            last_runs_item = TaskRun.from_dict(last_runs_item_data)

            last_runs.append(last_runs_item)

        status = ArbexStatus(d.pop("status"))

        updated_at = isoparse(d.pop("updated_at"))

        workspace_id = d.pop("workspace_id")

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        task_get_by_id_response_200 = cls(
            created_at=created_at,
            id=id,
            input_data=input_data,
            killed=killed,
            last_runs=last_runs,
            status=status,
            updated_at=updated_at,
            workspace_id=workspace_id,
            name=name,
        )

        task_get_by_id_response_200.additional_properties = d
        return task_get_by_id_response_200

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
