from collections.abc import Mapping
from typing import (
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

from ..models.orchestration_status import OrchestrationStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetOrchestrationByIdResponse")


@_attrs_define
class GetOrchestrationByIdResponse:
    """
    Attributes:
        file_name (str):
        id (UUID):
        owner_id (str):
        sha (str):
        status (OrchestrationStatus): The possible states an [Orchestration]'s Packaging status can be in.
        workspace_id (int):
        created_at (Union[None, Unset, str]):
        name (Union[None, Unset, str]):
        task_id (Union[None, UUID, Unset, int]):
    """

    file_name: str
    id: UUID
    owner_id: str
    sha: str
    status: OrchestrationStatus
    workspace_id: int
    created_at: Union[None, Unset, str] = UNSET
    name: Union[None, Unset, str] = UNSET
    task_id: Union[None, UUID, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file_name = self.file_name

        id = str(self.id)

        owner_id = self.owner_id

        sha = self.sha

        status = self.status.value

        workspace_id = self.workspace_id

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        name: Union[None, Unset, str]
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        task_id: Union[None, Unset, int, str]
        if isinstance(self.task_id, Unset):
            task_id = UNSET
        elif isinstance(self.task_id, UUID):
            task_id = str(self.task_id)
        else:
            task_id = self.task_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file_name": file_name,
                "id": id,
                "owner_id": owner_id,
                "sha": sha,
                "status": status,
                "workspace_id": workspace_id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if name is not UNSET:
            field_dict["name"] = name
        if task_id is not UNSET:
            field_dict["task_id"] = task_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file_name = d.pop("file_name")

        id = UUID(d.pop("id"))

        owner_id = d.pop("owner_id")

        sha = d.pop("sha")

        status = OrchestrationStatus(d.pop("status"))

        workspace_id = d.pop("workspace_id")

        def _parse_created_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_task_id(data: object) -> Union[None, UUID, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                componentsschemas_event_id_type_1 = UUID(data)

                return componentsschemas_event_id_type_1
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset, int], data)

        task_id = _parse_task_id(d.pop("task_id", UNSET))

        get_orchestration_by_id_response = cls(
            file_name=file_name,
            id=id,
            owner_id=owner_id,
            sha=sha,
            status=status,
            workspace_id=workspace_id,
            created_at=created_at,
            name=name,
            task_id=task_id,
        )

        get_orchestration_by_id_response.additional_properties = d
        return get_orchestration_by_id_response

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
