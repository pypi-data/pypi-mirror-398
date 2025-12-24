from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="RequestContinuousBatchingConfig")


@_attrs_define
class RequestContinuousBatchingConfig:
    """
    Attributes:
        max_concurrent_batch_size (int):
    """

    max_concurrent_batch_size: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        max_concurrent_batch_size = self.max_concurrent_batch_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "max_concurrent_batch_size": max_concurrent_batch_size,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        max_concurrent_batch_size = d.pop("max_concurrent_batch_size")

        request_continuous_batching_config = cls(
            max_concurrent_batch_size=max_concurrent_batch_size,
        )

        request_continuous_batching_config.additional_properties = d
        return request_continuous_batching_config

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
