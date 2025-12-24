"""This module features the modelling dataclasses for
received events through NATS.

In particular, it features a one-to-one mapping of the ModelConversionUpdate
config found in `wallsvc`
(more info here: https://github.com/WallarooLabs/platform/blob/main/conductor/wallsvc/src/models/event.rs).
"""

import base64
import logging
from typing import Any, Optional, Union

import pyarrow as pa
from pydantic import (
    BaseModel,
    ConfigDict,
    DirectoryPath,
    EncodedBytes,
    EncoderProtocol,
    Field,
    FilePath,
    model_validator,
)
from typing_extensions import Annotated

from pydata_util.nats.acceleration import (
    Acceleration,
    AccelerationWithConfig,
    AccelerationWithConfigFactory,
    SupportedAccelerations,
)
from pydata_util.nats.framework_config import FrameworkConfig
from pydata_util.types import SupportedFrameworks

logger = logging.getLogger(__name__)


class Conversion(BaseModel):
    """This dataclass stores data related to
    the conversion of a model."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
    )

    accel: Acceleration
    framework: SupportedFrameworks
    framework_config: Optional[FrameworkConfig] = Field(
        default=None,
        validate_default=True,
        description="The framework config for the given framework.",
    )

    @property
    def model_accel(self) -> Union[SupportedAccelerations, AccelerationWithConfig]:
        """Return the acceleration of the model."""
        return self.accel.root

    @model_validator(mode="before")
    @classmethod
    def parse_acceleration(cls, data: Any) -> Any:
        """Parse the acceleration, by distinguishing between a string for a
        supported acceleration and a dict for an acceleration with a config."""
        accel_inner = data.get("accel")

        if isinstance(accel_inner, str):
            data["accel"] = SupportedAccelerations(accel_inner)
        elif accel_inner is None:
            data["accel"] = SupportedAccelerations._None
        elif isinstance(accel_inner, dict):
            if len(accel_inner) != 1:
                raise ValueError(
                    "Acceleration with config must have exactly one key "
                    "corresponding to the acceleration type"
                )

            accel_key = next(iter(accel_inner))
            data["accel"] = AccelerationWithConfigFactory().create(
                SupportedAccelerations(accel_key), **accel_inner[accel_key]
            )

        return data

    @model_validator(mode="before")
    @classmethod
    def split_task_from_framework_if_necessary(cls, data: Any) -> Any:
        """Split the task from the framework if necessary and assign it to
        the settings attribute."""
        # Until we separate tasks from framework in the HuggingFace case
        framework = data.get("framework")
        if framework.startswith("hugging-face"):
            data["framework"] = "hugging-face"
            data["settings"] = {"task": framework.split("hugging-face-")[1]}

        return data

    @model_validator(mode="after")
    def validate_framework(self) -> "Conversion":
        """Validate that the framework requires a config."""
        if not isinstance(self.framework, SupportedFrameworks):
            framework = SupportedFrameworks(self.framework)
        else:
            framework = self.framework

        if framework.requires_config():
            if self.framework_config is None:
                raise ValueError(
                    f"Framework `{framework}` requires a config, but no config "
                    "was provided"
                )
            if framework != self.framework_config.framework:
                raise ValueError(
                    f"Framework `{framework}` does not match config framework "
                    f"`{self.framework_config.framework}`"
                )
        return self


class FileInfo(BaseModel):
    """This dataclass stores data related to
    a model file."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="allow",
    )

    sha: str
    file_name: Union[FilePath, DirectoryPath]


class ModelVersion(BaseModel):
    """This dataclass stores data related to
    a model version."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
    )

    name: str
    conversion: Conversion
    workspace_id: int
    file_info: FileInfo


class ContinuousBatchingConfig(BaseModel):
    """This dataclass stores the continuous batching config."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="allow",
    )

    max_concurrent_batch_size: int


class SchemaEncoder(EncoderProtocol):
    """This class implements a custom encoder/decoder
    for PyArrow schemas."""

    @classmethod
    def decode(cls, data: bytes) -> pa.Schema:
        """Decode the incoming bytes to a PyArrow schema.

        :param data: The encoded schema.
        """
        if data == b"**undecodable**":
            raise ValueError("Cannot decode data")

        decoded = base64.b64decode(data)

        try:
            with pa.ipc.open_stream(decoded) as reader:
                return reader.schema
        except OSError as exc:
            message = f"Cannot decode schema: {decoded!r}"
            logger.exception(message)
            raise ValueError(message) from exc

    @classmethod
    def encode(cls, value: pa.Schema) -> str:  # type: ignore[override]
        """Encode the PyArrow schema to byte string."""
        return base64.b64encode(value.serialize()).decode("utf-8")


EncodedSchema = Annotated[bytes, EncodedBytes(encoder=SchemaEncoder)]


class ModelConfig(BaseModel):
    """This dataclass stores the configuration
    related to a model."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="allow",
    )

    input_schema: EncodedSchema
    output_schema: EncodedSchema
    continuous_batching_config: Optional[ContinuousBatchingConfig] = None


class ConfiguredModelVersion(BaseModel):
    """This dataclass stores data related to
    a configured model."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
        protected_namespaces=(),
    )

    model_version: ModelVersion
    config: ModelConfig


class ModelPackagingUpdateEvent(BaseModel):
    """This dataclass stores data related to a model packaging update.
    For more info see: https://github.com/WallarooLabs/platform/blob/main/conductor/wallsvc/src/models/event.rs#L30.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
    )

    model: ConfiguredModelVersion


class ModelConversionUpdateEvent(ModelPackagingUpdateEvent):
    """This dataclass stores data related to a ModelUpdate event.
    It can be used either for model conversion or model packaging messages.
    For more info see: https://github.com/WallarooLabs/platform/blob/main/conductor/wallsvc/src/models/event.rs#L79
    respectively."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        use_enum_values=True,
        extra="allow",
    )

    orig_path: Optional[str] = None
