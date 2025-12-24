from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.auto_scale_config_type_1_type import AutoScaleConfigType1Type

T = TypeVar("T", bound="AutoScaleConfigType1")


@_attrs_define
class AutoScaleConfigType1:
    """
    Attributes:
        replica_max (int):
        replica_min (int):
        type_ (AutoScaleConfigType1Type):
    """

    replica_max: int
    replica_min: int
    type_: AutoScaleConfigType1Type
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        replica_max = self.replica_max

        replica_min = self.replica_min

        type_ = self.type_.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "replica_max": replica_max,
                "replica_min": replica_min,
                "type": type_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        replica_max = d.pop("replica_max")

        replica_min = d.pop("replica_min")

        type_ = AutoScaleConfigType1Type(d.pop("type"))

        auto_scale_config_type_1 = cls(
            replica_max=replica_max,
            replica_min=replica_min,
            type_=type_,
        )

        auto_scale_config_type_1.additional_properties = d
        return auto_scale_config_type_1

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
