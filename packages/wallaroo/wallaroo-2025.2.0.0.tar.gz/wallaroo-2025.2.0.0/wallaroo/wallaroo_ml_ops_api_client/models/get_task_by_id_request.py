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

T = TypeVar("T", bound="GetTaskByIdRequest")


@_attrs_define
class GetTaskByIdRequest:
    """
    Attributes:
        id (UUID):
        run_limit (Union[None, Unset, int]):
    """

    id: UUID
    run_limit: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        run_limit: Union[None, Unset, int]
        if isinstance(self.run_limit, Unset):
            run_limit = UNSET
        else:
            run_limit = self.run_limit

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if run_limit is not UNSET:
            field_dict["run_limit"] = run_limit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        def _parse_run_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        run_limit = _parse_run_limit(d.pop("run_limit", UNSET))

        get_task_by_id_request = cls(
            id=id,
            run_limit=run_limit,
        )

        get_task_by_id_request.additional_properties = d
        return get_task_by_id_request

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
