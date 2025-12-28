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

from ..models.auto_scale_config_type_0_type import AutoScaleConfigType0Type
from ..types import UNSET, Unset

T = TypeVar("T", bound="AutoScaleConfigType0")


@_attrs_define
class AutoScaleConfigType0:
    """
    Attributes:
        type_ (AutoScaleConfigType0Type):
        cpu_utilization (Union[Unset, float]):
        replica_max (Union[None, Unset, int]):
        replica_min (Union[None, Unset, int]):
    """

    type_: AutoScaleConfigType0Type
    cpu_utilization: Union[Unset, float] = UNSET
    replica_max: Union[None, Unset, int] = UNSET
    replica_min: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        cpu_utilization = self.cpu_utilization

        replica_max: Union[None, Unset, int]
        if isinstance(self.replica_max, Unset):
            replica_max = UNSET
        else:
            replica_max = self.replica_max

        replica_min: Union[None, Unset, int]
        if isinstance(self.replica_min, Unset):
            replica_min = UNSET
        else:
            replica_min = self.replica_min

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if cpu_utilization is not UNSET:
            field_dict["cpu_utilization"] = cpu_utilization
        if replica_max is not UNSET:
            field_dict["replica_max"] = replica_max
        if replica_min is not UNSET:
            field_dict["replica_min"] = replica_min

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = AutoScaleConfigType0Type(d.pop("type"))

        cpu_utilization = d.pop("cpu_utilization", UNSET)

        def _parse_replica_max(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        replica_max = _parse_replica_max(d.pop("replica_max", UNSET))

        def _parse_replica_min(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        replica_min = _parse_replica_min(d.pop("replica_min", UNSET))

        auto_scale_config_type_0 = cls(
            type_=type_,
            cpu_utilization=cpu_utilization,
            replica_max=replica_max,
            replica_min=replica_min,
        )

        auto_scale_config_type_0.additional_properties = d
        return auto_scale_config_type_0

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
