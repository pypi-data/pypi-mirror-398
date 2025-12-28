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

from ..types import UNSET, Unset

T = TypeVar("T", bound="RequestDynamicBatchingConfig")


@_attrs_define
class RequestDynamicBatchingConfig:
    """
    Attributes:
        batch_size_limit (Union[None, Unset, int]):
        batch_size_target (Union[None, Unset, int]):
        max_batch_delay_ms (Union[None, Unset, int]):
    """

    batch_size_limit: Union[None, Unset, int] = UNSET
    batch_size_target: Union[None, Unset, int] = UNSET
    max_batch_delay_ms: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        batch_size_limit: Union[None, Unset, int]
        if isinstance(self.batch_size_limit, Unset):
            batch_size_limit = UNSET
        else:
            batch_size_limit = self.batch_size_limit

        batch_size_target: Union[None, Unset, int]
        if isinstance(self.batch_size_target, Unset):
            batch_size_target = UNSET
        else:
            batch_size_target = self.batch_size_target

        max_batch_delay_ms: Union[None, Unset, int]
        if isinstance(self.max_batch_delay_ms, Unset):
            max_batch_delay_ms = UNSET
        else:
            max_batch_delay_ms = self.max_batch_delay_ms

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if batch_size_limit is not UNSET:
            field_dict["batch_size_limit"] = batch_size_limit
        if batch_size_target is not UNSET:
            field_dict["batch_size_target"] = batch_size_target
        if max_batch_delay_ms is not UNSET:
            field_dict["max_batch_delay_ms"] = max_batch_delay_ms

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_batch_size_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        batch_size_limit = _parse_batch_size_limit(d.pop("batch_size_limit", UNSET))

        def _parse_batch_size_target(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        batch_size_target = _parse_batch_size_target(d.pop("batch_size_target", UNSET))

        def _parse_max_batch_delay_ms(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_batch_delay_ms = _parse_max_batch_delay_ms(
            d.pop("max_batch_delay_ms", UNSET)
        )

        request_dynamic_batching_config = cls(
            batch_size_limit=batch_size_limit,
            batch_size_target=batch_size_target,
            max_batch_delay_ms=max_batch_delay_ms,
        )

        request_dynamic_batching_config.additional_properties = d
        return request_dynamic_batching_config

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
