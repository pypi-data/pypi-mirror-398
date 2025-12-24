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

from ..models.status_get_deployment_response_200_helm_item_info_health import (
    StatusGetDeploymentResponse200HelmItemInfoHealth,
)
from ..models.status_get_deployment_response_200_helm_item_info_status import (
    StatusGetDeploymentResponse200HelmItemInfoStatus,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.status_get_deployment_response_200_helm_item_info_labels import (
        StatusGetDeploymentResponse200HelmItemInfoLabels,
    )


T = TypeVar("T", bound="StatusGetDeploymentResponse200HelmItemInfo")


@_attrs_define
class StatusGetDeploymentResponse200HelmItemInfo:
    """
    Attributes:
        name (str):  Pod name.
        status (StatusGetDeploymentResponse200HelmItemInfoStatus):  Pod status.
        details (list[str]):  Details from kubernetes about the pod state.
        labels (StatusGetDeploymentResponse200HelmItemInfoLabels):  Kubernetes labels for the pod
        health (StatusGetDeploymentResponse200HelmItemInfoHealth):  The health of the pod.
        ip (Union[None, Unset, str]):  Pod IP address, if known.
        reason (Union[None, Unset, str]):  Reason for the current pod status, if available.
        required_cpu (Union[None, Unset, str]):  Minimum CPU required by the engine, if known.
        required_memory (Union[None, Unset, str]):  Memory required by the engine, if known.
    """

    name: str
    status: StatusGetDeploymentResponse200HelmItemInfoStatus
    details: list[str]
    labels: "StatusGetDeploymentResponse200HelmItemInfoLabels"
    health: StatusGetDeploymentResponse200HelmItemInfoHealth
    ip: Union[None, Unset, str] = UNSET
    reason: Union[None, Unset, str] = UNSET
    required_cpu: Union[None, Unset, str] = UNSET
    required_memory: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        status = self.status.value

        details = self.details

        labels = self.labels.to_dict()

        health = self.health.value

        ip: Union[None, Unset, str]
        if isinstance(self.ip, Unset):
            ip = UNSET
        else:
            ip = self.ip

        reason: Union[None, Unset, str]
        if isinstance(self.reason, Unset):
            reason = UNSET
        else:
            reason = self.reason

        required_cpu: Union[None, Unset, str]
        if isinstance(self.required_cpu, Unset):
            required_cpu = UNSET
        else:
            required_cpu = self.required_cpu

        required_memory: Union[None, Unset, str]
        if isinstance(self.required_memory, Unset):
            required_memory = UNSET
        else:
            required_memory = self.required_memory

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "status": status,
                "details": details,
                "labels": labels,
                "health": health,
            }
        )
        if ip is not UNSET:
            field_dict["ip"] = ip
        if reason is not UNSET:
            field_dict["reason"] = reason
        if required_cpu is not UNSET:
            field_dict["required_cpu"] = required_cpu
        if required_memory is not UNSET:
            field_dict["required_memory"] = required_memory

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.status_get_deployment_response_200_helm_item_info_labels import (
            StatusGetDeploymentResponse200HelmItemInfoLabels,
        )

        d = dict(src_dict)
        name = d.pop("name")

        status = StatusGetDeploymentResponse200HelmItemInfoStatus(d.pop("status"))

        details = cast(list[str], d.pop("details"))

        labels = StatusGetDeploymentResponse200HelmItemInfoLabels.from_dict(
            d.pop("labels")
        )

        health = StatusGetDeploymentResponse200HelmItemInfoHealth(d.pop("health"))

        def _parse_ip(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        ip = _parse_ip(d.pop("ip", UNSET))

        def _parse_reason(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        reason = _parse_reason(d.pop("reason", UNSET))

        def _parse_required_cpu(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        required_cpu = _parse_required_cpu(d.pop("required_cpu", UNSET))

        def _parse_required_memory(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        required_memory = _parse_required_memory(d.pop("required_memory", UNSET))

        status_get_deployment_response_200_helm_item_info = cls(
            name=name,
            status=status,
            details=details,
            labels=labels,
            health=health,
            ip=ip,
            reason=reason,
            required_cpu=required_cpu,
            required_memory=required_memory,
        )

        status_get_deployment_response_200_helm_item_info.additional_properties = d
        return status_get_deployment_response_200_helm_item_info

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
