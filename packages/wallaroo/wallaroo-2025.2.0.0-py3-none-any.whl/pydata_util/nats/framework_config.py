"""This module contains the framework configs for the different frameworks."""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from pydata_util.creation.abstract_factory import AbstractFactory
from pydata_util.types import SupportedFrameworks


class Quantization(str, Enum):
    """This class defines the supported quantizations for VLLMConfig."""

    AQLM = "aqlm"
    AWQ = "awq"
    AWQ_MARLIN = "awq_marlin"
    BITSANDBYTES = "bitsandbytes"
    COMPRESSED_TENSORS = "compressed-tensors"
    DEEPSPEEDFP = "deepspeedfp"
    EXPERTS_INT8 = "experts_int8"
    FBGEMM_FP8 = "fbgemm_fp8"
    FP8 = "fp8"
    GGUF = "gguf"
    GPTQ = "gptq"
    GPTQ_MARLIN = "gptq_marlin"
    GPTQ_MARLIN24 = "gptq_marlin24"
    HQQ = "hqq"
    IPEX = "ipex"
    MARLIN = "marlin"
    MODELOPT = "modelopt"
    MXFP6 = "mxfp6"  # only supported for `Acceleration.QAIC`
    NEURON_QUANT = "neuron_quant"
    NONE = "none"
    QQQ = "qqq"
    TPU_INT8 = "tpu_int8"


class KvCacheDtype(str, Enum):
    """This class defines the supported KV cache data types for VLLMConfig."""

    AUTO = "auto"
    FP8 = "fp8"
    FP8_E4M3 = "fp8_e4m3"
    FP8_E5M2 = "fp8_e5m2"
    MXINT8 = "mxint8"  # only supported for `Acceleration.QAIC`


class BaseFrameworkConfig(BaseModel, ABC):
    """
    A base class for all framework configs.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        use_enum_values=True,
        protected_namespaces=(),
    )

    @property
    @abstractmethod
    def framework(self) -> SupportedFrameworks:
        """The framework that this config is for."""


class CustomConfig(BaseFrameworkConfig):
    """
    A config for a custom framework.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="allow",
        use_enum_values=True,
        protected_namespaces=(),
    )

    model_path: Path = Field(
        description="The full path of the model, including the base directory of the extracted zip file. Defaults to './model/'.",  # noqa: E501
        default=Path("./model/"),
    )

    @property
    def framework(self) -> SupportedFrameworks:
        return SupportedFrameworks.CUSTOM


class VLLMConfig(BaseFrameworkConfig):
    """
    A config for the VLLM framework.
    """

    device_group: Optional[List[int]] = Field(
        default=None,
        validate_default=True,
        description="List of device ids to compile the model for that is only supported for `Acceleration.QAIC`. Defaults to `None`.",  # noqa: E501
    )
    gpu_memory_utilization: Optional[float] = Field(
        default=0.9,
        validate_default=True,
        description="The percentage of GPU memory to use. Defaults to 0.9.",
    )
    kv_cache_dtype: Optional[KvCacheDtype] = Field(
        default=KvCacheDtype.AUTO,
        validate_default=True,
        description="The data type of the KV cache. Defaults to 'auto'.",
    )
    max_model_len: Optional[int] = Field(
        default=None,
        validate_default=True,
        description="The maximum length of the model. Defaults to None.",
    )
    max_num_seqs: int = Field(
        default=256,
        validate_default=True,
        description="The maximum number of sequences to run in parallel. Defaults to None.",  # noqa: E501
    )
    max_seq_len_to_capture: Optional[int] = Field(
        default=8192,
        validate_default=True,
        description="The maximum length of the sequences to capture. Defaults to 8192.",
    )
    quantization: Optional[Quantization] = Field(
        default=Quantization.NONE,
        validate_default=True,
        description="The quantization to use. Defaults to 'none'.",
    )
    block_size: Optional[int] = Field(
        default=None,
        validate_default=True,
        description="The block size to use for the model. Recommended to set to `32` for better performance with `Acceleration::Qaic`. Defaults to `None`.",  # noqa: E501
    )

    @field_validator("quantization", mode="after")
    @classmethod
    def parse_quantization(cls, value):
        """Parse the quantization to the appropriate value."""
        return None if value == Quantization.NONE else value

    @field_serializer("quantization")
    @classmethod
    def serialize_quantization(cls, value):
        """Serialize the quantization to the appropriate value."""
        return "none" if value is None else value

    @property
    def framework(self) -> SupportedFrameworks:
        return SupportedFrameworks.VLLM


class FrameworkConfig(BaseModel, ABC):
    """
    This class represents a framework config as it arrives from the NATS message.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        use_enum_values=True,
        protected_namespaces=(),
    )

    framework: SupportedFrameworks = Field(
        description="The framework that this config is for.",
    )
    config: Optional[Union[VLLMConfig, CustomConfig]] = Field(
        default=None,
        validate_default=True,
        description="The config for the framework.",
    )

    @model_validator(mode="before")
    @classmethod
    def validate_and_convert_config(cls, data: Any) -> Any:
        """Validate the config and convert it to the appropriate type."""
        if not isinstance(data, dict):
            return data

        config, framework = data.get("config"), data["framework"]

        if config is None:
            # If the config is not provided, create a default config for the framework
            data["config"] = FrameworkConfigFactory().create(framework)

        if isinstance(config, dict):
            # If the config is a dictionary, create a config for the framework
            data["config"] = FrameworkConfigFactory().create(framework, **config)
        else:
            # If the config is already a config object, just use it
            data["config"] = config

        return data

    @model_validator(mode="after")
    def validate_framework(self) -> "FrameworkConfig":
        """Validate that the framework matches the config's framework."""
        if not isinstance(self.framework, SupportedFrameworks):
            framework = SupportedFrameworks(self.framework)
        else:
            framework = self.framework

        if framework != self.config.framework:  # type: ignore[union-attr]
            raise ValueError(
                f"Framework `{framework}` does not match config framework "
                f"`{self.config.framework}`"  # type: ignore[union-attr]
            )
        return self


class FrameworkConfigFactory(AbstractFactory):
    """A factory for creating framework configs."""

    @property
    def subclass_creators(self) -> dict:
        """Returns a dictionary with keys corresponding to subclass names and values
        corresponding to the subclass creator functions."""
        return {
            SupportedFrameworks.VLLM: VLLMConfig,
            SupportedFrameworks.CUSTOM: CustomConfig,
        }
