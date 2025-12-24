from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="QaicConfig")


@_attrs_define
class QaicConfig:
    """
    Attributes:
        aic_enable_depth_first (Union[Unset, bool]): Enables DFS with default memory size. Default: False.
        ctx_len (Union[Unset, int]): Maximum context that the compiled model can remember. Default: 128.
        full_batch_size (Union[Unset, int]): Maximum number of sequences per iteration. Set to enable continuous
            batching mode. Default: 8.
        mxfp6_matmul (Union[Unset, bool]): Enable compilation for MXFP6 precision. Default: False.
        mxint8_kv_cache (Union[Unset, bool]): Compress Present/Past KV to MXINT8. Default: False.
        num_cores (Union[Unset, int]): Number of cores used to compile the model. Default: 16.
        num_devices (Union[Unset, int]): Number of SoCs in a given card to compile the model for. Each card (e.g. AI100)
            has 4 SoCs. Default: 1.
        prefill_seq_len (Union[Unset, int]): The length of the Prefill prompt. Default: 32.
    """

    aic_enable_depth_first: Union[Unset, bool] = False
    ctx_len: Union[Unset, int] = 128
    full_batch_size: Union[Unset, int] = 8
    mxfp6_matmul: Union[Unset, bool] = False
    mxint8_kv_cache: Union[Unset, bool] = False
    num_cores: Union[Unset, int] = 16
    num_devices: Union[Unset, int] = 1
    prefill_seq_len: Union[Unset, int] = 32
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        aic_enable_depth_first = self.aic_enable_depth_first

        ctx_len = self.ctx_len

        full_batch_size = self.full_batch_size

        mxfp6_matmul = self.mxfp6_matmul

        mxint8_kv_cache = self.mxint8_kv_cache

        num_cores = self.num_cores

        num_devices = self.num_devices

        prefill_seq_len = self.prefill_seq_len

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if aic_enable_depth_first is not UNSET:
            field_dict["aic_enable_depth_first"] = aic_enable_depth_first
        if ctx_len is not UNSET:
            field_dict["ctx_len"] = ctx_len
        if full_batch_size is not UNSET:
            field_dict["full_batch_size"] = full_batch_size
        if mxfp6_matmul is not UNSET:
            field_dict["mxfp6_matmul"] = mxfp6_matmul
        if mxint8_kv_cache is not UNSET:
            field_dict["mxint8_kv_cache"] = mxint8_kv_cache
        if num_cores is not UNSET:
            field_dict["num_cores"] = num_cores
        if num_devices is not UNSET:
            field_dict["num_devices"] = num_devices
        if prefill_seq_len is not UNSET:
            field_dict["prefill_seq_len"] = prefill_seq_len

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        aic_enable_depth_first = d.pop("aic_enable_depth_first", UNSET)

        ctx_len = d.pop("ctx_len", UNSET)

        full_batch_size = d.pop("full_batch_size", UNSET)

        mxfp6_matmul = d.pop("mxfp6_matmul", UNSET)

        mxint8_kv_cache = d.pop("mxint8_kv_cache", UNSET)

        num_cores = d.pop("num_cores", UNSET)

        num_devices = d.pop("num_devices", UNSET)

        prefill_seq_len = d.pop("prefill_seq_len", UNSET)

        qaic_config = cls(
            aic_enable_depth_first=aic_enable_depth_first,
            ctx_len=ctx_len,
            full_batch_size=full_batch_size,
            mxfp6_matmul=mxfp6_matmul,
            mxint8_kv_cache=mxint8_kv_cache,
            num_cores=num_cores,
            num_devices=num_devices,
            prefill_seq_len=prefill_seq_len,
        )

        qaic_config.additional_properties = d
        return qaic_config

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
