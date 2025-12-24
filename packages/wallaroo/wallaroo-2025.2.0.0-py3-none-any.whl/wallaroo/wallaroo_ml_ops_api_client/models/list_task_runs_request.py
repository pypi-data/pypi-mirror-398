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

from ..models.list_task_runs_request_status import ListTaskRunsRequestStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.list_task_runs_request_time_range_type_0_item import (
        ListTaskRunsRequestTimeRangeType0Item,
    )


T = TypeVar("T", bound="ListTaskRunsRequest")


@_attrs_define
class ListTaskRunsRequest:
    """
    Attributes:
        task_id (UUID):
        limit (Union[None, Unset, int]):
        status (Union[ListTaskRunsRequestStatus, None, Unset]):
        time_range (Union[None, Unset, list['ListTaskRunsRequestTimeRangeType0Item']]):
    """

    task_id: UUID
    limit: Union[None, Unset, int] = UNSET
    status: Union[ListTaskRunsRequestStatus, None, Unset] = UNSET
    time_range: Union[None, Unset, list["ListTaskRunsRequestTimeRangeType0Item"]] = (
        UNSET
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        task_id = str(self.task_id)

        limit: Union[None, Unset, int]
        if isinstance(self.limit, Unset):
            limit = UNSET
        else:
            limit = self.limit

        status: Union[None, Unset, str]
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, ListTaskRunsRequestStatus):
            status = self.status.value
        else:
            status = self.status

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
                "task_id": task_id,
            }
        )
        if limit is not UNSET:
            field_dict["limit"] = limit
        if status is not UNSET:
            field_dict["status"] = status
        if time_range is not UNSET:
            field_dict["time_range"] = time_range

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.list_task_runs_request_time_range_type_0_item import (
            ListTaskRunsRequestTimeRangeType0Item,
        )

        d = dict(src_dict)
        task_id = UUID(d.pop("task_id"))

        def _parse_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        limit = _parse_limit(d.pop("limit", UNSET))

        def _parse_status(
            data: object,
        ) -> Union[ListTaskRunsRequestStatus, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_1 = ListTaskRunsRequestStatus(data)

                return status_type_1
            except:  # noqa: E722
                pass
            return cast(Union[ListTaskRunsRequestStatus, None, Unset], data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_time_range(
            data: object,
        ) -> Union[None, Unset, list["ListTaskRunsRequestTimeRangeType0Item"]]:
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
                        ListTaskRunsRequestTimeRangeType0Item.from_dict(
                            time_range_type_0_item_data
                        )
                    )

                    time_range_type_0.append(time_range_type_0_item)

                return time_range_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[None, Unset, list["ListTaskRunsRequestTimeRangeType0Item"]], data
            )

        time_range = _parse_time_range(d.pop("time_range", UNSET))

        list_task_runs_request = cls(
            task_id=task_id,
            limit=limit,
            status=status,
            time_range=time_range,
        )

        list_task_runs_request.additional_properties = d
        return list_task_runs_request

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
