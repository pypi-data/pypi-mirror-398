"""This modules includes the dataclasses related to the acceleration."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_serializer

from pydata_util.creation.abstract_factory import AbstractFactory


class SupportedAccelerations(str, Enum):
    """This class defines the supported accelerations."""

    _None = "none"
    CUDA = "cuda"
    Jetson = "jetson"
    OpenVINO = "openvino"
    QAIC = "qaic"


class AccelerationWithConfig(BaseModel, ABC):
    """An acceleration with a config."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        use_enum_values=True,
        protected_namespaces=(),
    )

    @property
    @abstractmethod
    def accel(self) -> SupportedAccelerations:
        """Return the acceleration associated with the config."""


class QaicConfig(AccelerationWithConfig):
    """A config for the `QAIC` acceleration."""

    num_cores: int = Field(
        ge=1,
        default=16,
        description="Number of cores used to compile the model. Defaults to `16`.",
    )
    num_devices: int = Field(
        ge=1,
        default=1,
        description="Number of SoCs in a given card to compile the model for. Each card (e.g. AI100) has 4 SoCs. Defaults to `1`.",  # noqa: E501
    )
    ctx_len: int = Field(
        ge=1,
        default=128,
        description="Maximum context that the compiled model can remember. Defaults to `128`.",  # noqa: E501
    )
    prefill_seq_len: int = Field(
        ge=1,
        default=32,
        description="The length of the Prefill prompt. Defaults to `32`.",
    )
    full_batch_size: int = Field(
        default=8,
        validate_default=True,
        ge=1,
        description="Maximum number of sequences per iteration. Set to enable continuous batching mode. Defaults to `8`.",  # noqa: E501
    )
    mxfp6_matmul: bool = Field(
        default=False,
        description="Enable compilation for MXFP6 precision. Defaults to `False`.",
    )
    mxint8_kv_cache: bool = Field(
        default=False,
        description="Compress Present/Past KV to MXINT8. Defaults to `False`.",
    )
    aic_enable_depth_first: bool = Field(
        default=False,
        description="Enables DFS with default memory size. Defaults to `False`.",
    )

    @property
    def accel(self) -> SupportedAccelerations:
        """Return the acceleration."""
        return SupportedAccelerations.QAIC


class Acceleration(RootModel[Union[SupportedAccelerations, AccelerationWithConfig]]):
    """This class defines the acceleration."""

    @model_serializer
    def serialize_model(self) -> Union[Dict[str, Any], SupportedAccelerations]:
        """Serialize the model taking into account the type of the acceleration."""
        if isinstance(self.root, AccelerationWithConfig):
            return {self.root.accel: self.root.model_dump()}
        return self.root


class AccelerationWithConfigFactory(AbstractFactory):
    """A factory for creating acceleration with configs."""

    @property
    def subclass_creators(self) -> dict:
        """Returns a dictionary with keys corresponding to subclass names and values
        corresponding to the subclass creator functions."""
        return {
            SupportedAccelerations.QAIC: QaicConfig,
        }
