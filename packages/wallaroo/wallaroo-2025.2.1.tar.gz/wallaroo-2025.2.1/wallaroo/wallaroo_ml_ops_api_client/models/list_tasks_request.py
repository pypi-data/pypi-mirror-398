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

from ..types import UNSET, Unset

T = TypeVar("T", bound="ListTasksRequest")


@_attrs_define
class ListTasksRequest:
    """
    Attributes:
        killed (Union[None, Unset, bool]):
        orch_id (Union[None, UUID, Unset]):
        orch_sha (Union[None, Unset, str]):
        run_limit (Union[None, Unset, int]):
        workspace_id (Union[None, Unset, int]):
    """

    killed: Union[None, Unset, bool] = UNSET
    orch_id: Union[None, UUID, Unset] = UNSET
    orch_sha: Union[None, Unset, str] = UNSET
    run_limit: Union[None, Unset, int] = UNSET
    workspace_id: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        killed: Union[None, Unset, bool]
        if isinstance(self.killed, Unset):
            killed = UNSET
        else:
            killed = self.killed

        orch_id: Union[None, Unset, str]
        if isinstance(self.orch_id, Unset):
            orch_id = UNSET
        elif isinstance(self.orch_id, UUID):
            orch_id = str(self.orch_id)
        else:
            orch_id = self.orch_id

        orch_sha: Union[None, Unset, str]
        if isinstance(self.orch_sha, Unset):
            orch_sha = UNSET
        else:
            orch_sha = self.orch_sha

        run_limit: Union[None, Unset, int]
        if isinstance(self.run_limit, Unset):
            run_limit = UNSET
        else:
            run_limit = self.run_limit

        workspace_id: Union[None, Unset, int]
        if isinstance(self.workspace_id, Unset):
            workspace_id = UNSET
        else:
            workspace_id = self.workspace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if killed is not UNSET:
            field_dict["killed"] = killed
        if orch_id is not UNSET:
            field_dict["orch_id"] = orch_id
        if orch_sha is not UNSET:
            field_dict["orch_sha"] = orch_sha
        if run_limit is not UNSET:
            field_dict["run_limit"] = run_limit
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_killed(data: object) -> Union[None, Unset, bool]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, bool], data)

        killed = _parse_killed(d.pop("killed", UNSET))

        def _parse_orch_id(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                orch_id_type_0 = UUID(data)

                return orch_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        orch_id = _parse_orch_id(d.pop("orch_id", UNSET))

        def _parse_orch_sha(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        orch_sha = _parse_orch_sha(d.pop("orch_sha", UNSET))

        def _parse_run_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        run_limit = _parse_run_limit(d.pop("run_limit", UNSET))

        def _parse_workspace_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        workspace_id = _parse_workspace_id(d.pop("workspace_id", UNSET))

        list_tasks_request = cls(
            killed=killed,
            orch_id=orch_id,
            orch_sha=orch_sha,
            run_limit=run_limit,
            workspace_id=workspace_id,
        )

        list_tasks_request.additional_properties = d
        return list_tasks_request

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
