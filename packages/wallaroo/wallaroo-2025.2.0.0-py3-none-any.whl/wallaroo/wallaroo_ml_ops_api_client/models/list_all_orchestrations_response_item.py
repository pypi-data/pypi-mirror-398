from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.orchestration import Orchestration
    from ..models.task import Task
    from ..models.workspace import Workspace


T = TypeVar("T", bound="ListAllOrchestrationsResponseItem")


@_attrs_define
class ListAllOrchestrationsResponseItem:
    """
    Attributes:
        orchestration (Orchestration): A struct that mirrors the data in Hasura's Orchestration table.
        tasks (list['Task']):
        workspace (Workspace):
    """

    orchestration: "Orchestration"
    tasks: list["Task"]
    workspace: "Workspace"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        orchestration = self.orchestration.to_dict()

        tasks = []
        for tasks_item_data in self.tasks:
            tasks_item = tasks_item_data.to_dict()
            tasks.append(tasks_item)

        workspace = self.workspace.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "orchestration": orchestration,
                "tasks": tasks,
                "workspace": workspace,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.orchestration import Orchestration
        from ..models.task import Task
        from ..models.workspace import Workspace

        d = dict(src_dict)
        orchestration = Orchestration.from_dict(d.pop("orchestration"))

        tasks = []
        _tasks = d.pop("tasks")
        for tasks_item_data in _tasks:
            tasks_item = Task.from_dict(tasks_item_data)

            tasks.append(tasks_item)

        workspace = Workspace.from_dict(d.pop("workspace"))

        list_all_orchestrations_response_item = cls(
            orchestration=orchestration,
            tasks=tasks,
            workspace=workspace,
        )

        list_all_orchestrations_response_item.additional_properties = d
        return list_all_orchestrations_response_item

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
