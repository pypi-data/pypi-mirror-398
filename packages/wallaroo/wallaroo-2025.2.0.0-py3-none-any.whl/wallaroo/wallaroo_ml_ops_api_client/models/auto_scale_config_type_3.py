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

from ..models.auto_scale_config_type_3_type import AutoScaleConfigType3Type
from ..types import UNSET, Unset

T = TypeVar("T", bound="AutoScaleConfigType3")


@_attrs_define
class AutoScaleConfigType3:
    """
    Attributes:
        type_ (AutoScaleConfigType3Type):
        cpu_utilization (Union[None, Unset, float]):
    """

    type_: AutoScaleConfigType3Type
    cpu_utilization: Union[None, Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        cpu_utilization: Union[None, Unset, float]
        if isinstance(self.cpu_utilization, Unset):
            cpu_utilization = UNSET
        else:
            cpu_utilization = self.cpu_utilization

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
            }
        )
        if cpu_utilization is not UNSET:
            field_dict["cpu_utilization"] = cpu_utilization

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = AutoScaleConfigType3Type(d.pop("type"))

        def _parse_cpu_utilization(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        cpu_utilization = _parse_cpu_utilization(d.pop("cpu_utilization", UNSET))

        auto_scale_config_type_3 = cls(
            type_=type_,
            cpu_utilization=cpu_utilization,
        )

        auto_scale_config_type_3.additional_properties = d
        return auto_scale_config_type_3

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
