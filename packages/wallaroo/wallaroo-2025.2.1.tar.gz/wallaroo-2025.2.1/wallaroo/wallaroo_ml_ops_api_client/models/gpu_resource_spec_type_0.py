from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="GpuResourceSpecType0")


@_attrs_define
class GpuResourceSpecType0:
    """
    Attributes:
        nvidia_comgpu (int):
    """

    nvidia_comgpu: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        nvidia_comgpu = self.nvidia_comgpu

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "nvidia.com/gpu": nvidia_comgpu,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        nvidia_comgpu = d.pop("nvidia.com/gpu")

        gpu_resource_spec_type_0 = cls(
            nvidia_comgpu=nvidia_comgpu,
        )

        gpu_resource_spec_type_0.additional_properties = d
        return gpu_resource_spec_type_0

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
