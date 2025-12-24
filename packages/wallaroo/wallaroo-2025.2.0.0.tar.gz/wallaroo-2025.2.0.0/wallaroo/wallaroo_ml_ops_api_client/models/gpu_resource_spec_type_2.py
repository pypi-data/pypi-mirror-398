from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="GpuResourceSpecType2")


@_attrs_define
class GpuResourceSpecType2:
    """
    Attributes:
        qualcomm_comqaic (int):
    """

    qualcomm_comqaic: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        qualcomm_comqaic = self.qualcomm_comqaic

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "qualcomm.com/qaic": qualcomm_comqaic,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        qualcomm_comqaic = d.pop("qualcomm.com/qaic")

        gpu_resource_spec_type_2 = cls(
            qualcomm_comqaic=qualcomm_comqaic,
        )

        gpu_resource_spec_type_2.additional_properties = d
        return gpu_resource_spec_type_2

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
