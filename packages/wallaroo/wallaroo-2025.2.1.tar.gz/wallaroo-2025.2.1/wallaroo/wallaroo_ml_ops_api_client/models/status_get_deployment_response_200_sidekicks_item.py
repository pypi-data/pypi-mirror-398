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

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.status_get_deployment_response_200_sidekicks_item_info import (
        StatusGetDeploymentResponse200SidekicksItemInfo,
    )


T = TypeVar("T", bound="StatusGetDeploymentResponse200SidekicksItem")


@_attrs_define
class StatusGetDeploymentResponse200SidekicksItem:
    """Sidekick engine deployment status.

    Attributes:
        info (StatusGetDeploymentResponse200SidekicksItemInfo):
        statuses (Union[None, Unset, str]):  Statuses of engine sidekick servers.
    """

    info: "StatusGetDeploymentResponse200SidekicksItemInfo"
    statuses: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        info = self.info.to_dict()

        statuses: Union[None, Unset, str]
        if isinstance(self.statuses, Unset):
            statuses = UNSET
        else:
            statuses = self.statuses

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "info": info,
            }
        )
        if statuses is not UNSET:
            field_dict["statuses"] = statuses

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.status_get_deployment_response_200_sidekicks_item_info import (
            StatusGetDeploymentResponse200SidekicksItemInfo,
        )

        d = dict(src_dict)
        info = StatusGetDeploymentResponse200SidekicksItemInfo.from_dict(d.pop("info"))

        def _parse_statuses(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        statuses = _parse_statuses(d.pop("statuses", UNSET))

        status_get_deployment_response_200_sidekicks_item = cls(
            info=info,
            statuses=statuses,
        )

        status_get_deployment_response_200_sidekicks_item.additional_properties = d
        return status_get_deployment_response_200_sidekicks_item

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
