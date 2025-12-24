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

from ..models.kv_cache_dtype import KvCacheDtype
from ..models.quantization import Quantization
from ..types import UNSET, Unset

T = TypeVar("T", bound="VLLMConfig")


@_attrs_define
class VLLMConfig:
    """
    Attributes:
        block_size (Union[None, Unset, int]): The block size to use for the model. Defaults to `None` but recommended to
            set to `32` for better performance with `Acceleration::Qaic`.
        device_group (Union[None, Unset, list[int]]): The list of device IDs to load the model on. Only required for
            `Acceleration::Qaic`.
        gpu_memory_utilization (Union[Unset, float]):  Default: 0.9.
        kv_cache_dtype (Union[Unset, KvCacheDtype]): KV cache data type options for vLLM models.
            See `--kv-cache-dtype` in [the vllm docs](https://docs.vllm.ai/en/v0.6.6/usage/engine_args.html) for details on
            supported options. Default: KvCacheDtype.AUTO.
        max_model_len (Union[None, Unset, int]):
        max_num_seqs (Union[Unset, int]):  Default: 256.
        max_seq_len_to_capture (Union[Unset, int]):  Default: 8192.
        quantization (Union[Unset, Quantization]): Quantization options for vLLM models.
            See `--quantization` in [the vllm docs](https://docs.vllm.ai/en/v0.6.6/usage/engine_args.html) for details on
            supported options. Default: Quantization.NONE.
    """

    block_size: Union[None, Unset, int] = UNSET
    device_group: Union[None, Unset, list[int]] = UNSET
    gpu_memory_utilization: Union[Unset, float] = 0.9
    kv_cache_dtype: Union[Unset, KvCacheDtype] = KvCacheDtype.AUTO
    max_model_len: Union[None, Unset, int] = UNSET
    max_num_seqs: Union[Unset, int] = 256
    max_seq_len_to_capture: Union[Unset, int] = 8192
    quantization: Union[Unset, Quantization] = Quantization.NONE
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        block_size: Union[None, Unset, int]
        if isinstance(self.block_size, Unset):
            block_size = UNSET
        else:
            block_size = self.block_size

        device_group: Union[None, Unset, list[int]]
        if isinstance(self.device_group, Unset):
            device_group = UNSET
        elif isinstance(self.device_group, list):
            device_group = self.device_group

        else:
            device_group = self.device_group

        gpu_memory_utilization = self.gpu_memory_utilization

        kv_cache_dtype: Union[Unset, str] = UNSET
        if not isinstance(self.kv_cache_dtype, Unset):
            kv_cache_dtype = self.kv_cache_dtype.value

        max_model_len: Union[None, Unset, int]
        if isinstance(self.max_model_len, Unset):
            max_model_len = UNSET
        else:
            max_model_len = self.max_model_len

        max_num_seqs = self.max_num_seqs

        max_seq_len_to_capture = self.max_seq_len_to_capture

        quantization: Union[Unset, str] = UNSET
        if not isinstance(self.quantization, Unset):
            quantization = self.quantization.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if block_size is not UNSET:
            field_dict["block_size"] = block_size
        if device_group is not UNSET:
            field_dict["device_group"] = device_group
        if gpu_memory_utilization is not UNSET:
            field_dict["gpu_memory_utilization"] = gpu_memory_utilization
        if kv_cache_dtype is not UNSET:
            field_dict["kv_cache_dtype"] = kv_cache_dtype
        if max_model_len is not UNSET:
            field_dict["max_model_len"] = max_model_len
        if max_num_seqs is not UNSET:
            field_dict["max_num_seqs"] = max_num_seqs
        if max_seq_len_to_capture is not UNSET:
            field_dict["max_seq_len_to_capture"] = max_seq_len_to_capture
        if quantization is not UNSET:
            field_dict["quantization"] = quantization

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_block_size(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        block_size = _parse_block_size(d.pop("block_size", UNSET))

        def _parse_device_group(data: object) -> Union[None, Unset, list[int]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                device_group_type_0 = cast(list[int], data)

                return device_group_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[int]], data)

        device_group = _parse_device_group(d.pop("device_group", UNSET))

        gpu_memory_utilization = d.pop("gpu_memory_utilization", UNSET)

        _kv_cache_dtype = d.pop("kv_cache_dtype", UNSET)
        kv_cache_dtype: Union[Unset, KvCacheDtype]
        if isinstance(_kv_cache_dtype, Unset):
            kv_cache_dtype = UNSET
        else:
            kv_cache_dtype = KvCacheDtype(_kv_cache_dtype)

        def _parse_max_model_len(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        max_model_len = _parse_max_model_len(d.pop("max_model_len", UNSET))

        max_num_seqs = d.pop("max_num_seqs", UNSET)

        max_seq_len_to_capture = d.pop("max_seq_len_to_capture", UNSET)

        _quantization = d.pop("quantization", UNSET)
        quantization: Union[Unset, Quantization]
        if isinstance(_quantization, Unset):
            quantization = UNSET
        else:
            quantization = Quantization(_quantization)

        vllm_config = cls(
            block_size=block_size,
            device_group=device_group,
            gpu_memory_utilization=gpu_memory_utilization,
            kv_cache_dtype=kv_cache_dtype,
            max_model_len=max_model_len,
            max_num_seqs=max_num_seqs,
            max_seq_len_to_capture=max_seq_len_to_capture,
            quantization=quantization,
        )

        vllm_config.additional_properties = d
        return vllm_config

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
