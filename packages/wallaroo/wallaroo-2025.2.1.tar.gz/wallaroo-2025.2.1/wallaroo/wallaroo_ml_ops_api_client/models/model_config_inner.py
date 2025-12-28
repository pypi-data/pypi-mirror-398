from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..models.runtime import Runtime
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.continuous_batching_config import ContinuousBatchingConfig
    from ..models.dynamic_batching_config import DynamicBatchingConfig
    from ..models.open_ai_config import OpenAiConfig


T = TypeVar("T", bound="ModelConfigInner")


@_attrs_define
class ModelConfigInner:
    """Model configuration (mirrors row in model_config table in database)

    Attributes:
        model_version_id (int):
        runtime (Runtime): Valid runtime types
        batch_config (Union[None, Unset, str]):
        continuous_batching_config (Union['ContinuousBatchingConfig', None, Unset]):
        dynamic_batching_config (Union['DynamicBatchingConfig', None, Unset]):
        filter_threshold (Union[None, Unset, float]):
        input_schema (Union[None, Unset, str]):
        openai (Union['OpenAiConfig', None, Unset]):
        output_schema (Union[None, Unset, str]):
        queue_depth (Union[None, Unset, int]):
        sidekick_uri (Union[None, Unset, str]):
        tensor_fields (Union[None, Unset, list[str]]):
    """

    model_version_id: int
    runtime: Runtime
    batch_config: Union[None, Unset, str] = UNSET
    continuous_batching_config: Union["ContinuousBatchingConfig", None, Unset] = UNSET
    dynamic_batching_config: Union["DynamicBatchingConfig", None, Unset] = UNSET
    filter_threshold: Union[None, Unset, float] = UNSET
    input_schema: Union[None, Unset, str] = UNSET
    openai: Union["OpenAiConfig", None, Unset] = UNSET
    output_schema: Union[None, Unset, str] = UNSET
    queue_depth: Union[None, Unset, int] = UNSET
    sidekick_uri: Union[None, Unset, str] = UNSET
    tensor_fields: Union[None, Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.continuous_batching_config import ContinuousBatchingConfig
        from ..models.dynamic_batching_config import DynamicBatchingConfig
        from ..models.open_ai_config import OpenAiConfig

        model_version_id = self.model_version_id

        runtime = self.runtime.value

        batch_config: Union[None, Unset, str]
        if isinstance(self.batch_config, Unset):
            batch_config = UNSET
        else:
            batch_config = self.batch_config

        continuous_batching_config: Union[None, Unset, dict[str, Any]]
        if isinstance(self.continuous_batching_config, Unset):
            continuous_batching_config = UNSET
        elif isinstance(self.continuous_batching_config, ContinuousBatchingConfig):
            continuous_batching_config = self.continuous_batching_config.to_dict()
        else:
            continuous_batching_config = self.continuous_batching_config

        dynamic_batching_config: Union[None, Unset, dict[str, Any]]
        if isinstance(self.dynamic_batching_config, Unset):
            dynamic_batching_config = UNSET
        elif isinstance(self.dynamic_batching_config, DynamicBatchingConfig):
            dynamic_batching_config = self.dynamic_batching_config.to_dict()
        else:
            dynamic_batching_config = self.dynamic_batching_config

        filter_threshold: Union[None, Unset, float]
        if isinstance(self.filter_threshold, Unset):
            filter_threshold = UNSET
        else:
            filter_threshold = self.filter_threshold

        input_schema: Union[None, Unset, str]
        if isinstance(self.input_schema, Unset):
            input_schema = UNSET
        else:
            input_schema = self.input_schema

        openai: Union[None, Unset, dict[str, Any]]
        if isinstance(self.openai, Unset):
            openai = UNSET
        elif isinstance(self.openai, OpenAiConfig):
            openai = self.openai.to_dict()
        else:
            openai = self.openai

        output_schema: Union[None, Unset, str]
        if isinstance(self.output_schema, Unset):
            output_schema = UNSET
        else:
            output_schema = self.output_schema

        queue_depth: Union[None, Unset, int]
        if isinstance(self.queue_depth, Unset):
            queue_depth = UNSET
        else:
            queue_depth = self.queue_depth

        sidekick_uri: Union[None, Unset, str]
        if isinstance(self.sidekick_uri, Unset):
            sidekick_uri = UNSET
        else:
            sidekick_uri = self.sidekick_uri

        tensor_fields: Union[None, Unset, list[str]]
        if isinstance(self.tensor_fields, Unset):
            tensor_fields = UNSET
        elif isinstance(self.tensor_fields, list):
            tensor_fields = self.tensor_fields

        else:
            tensor_fields = self.tensor_fields

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model_version_id": model_version_id,
                "runtime": runtime,
            }
        )
        if batch_config is not UNSET:
            field_dict["batch_config"] = batch_config
        if continuous_batching_config is not UNSET:
            field_dict["continuous_batching_config"] = continuous_batching_config
        if dynamic_batching_config is not UNSET:
            field_dict["dynamic_batching_config"] = dynamic_batching_config
        if filter_threshold is not UNSET:
            field_dict["filter_threshold"] = filter_threshold
        if input_schema is not UNSET:
            field_dict["input_schema"] = input_schema
        if openai is not UNSET:
            field_dict["openai"] = openai
        if output_schema is not UNSET:
            field_dict["output_schema"] = output_schema
        if queue_depth is not UNSET:
            field_dict["queue_depth"] = queue_depth
        if sidekick_uri is not UNSET:
            field_dict["sidekick_uri"] = sidekick_uri
        if tensor_fields is not UNSET:
            field_dict["tensor_fields"] = tensor_fields

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.continuous_batching_config import ContinuousBatchingConfig
        from ..models.dynamic_batching_config import DynamicBatchingConfig
        from ..models.open_ai_config import OpenAiConfig

        d = dict(src_dict)
        model_version_id = d.pop("model_version_id")

        runtime = Runtime(d.pop("runtime"))

        def _parse_batch_config(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        batch_config = _parse_batch_config(d.pop("batch_config", UNSET))

        def _parse_continuous_batching_config(
            data: object,
        ) -> Union["ContinuousBatchingConfig", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                continuous_batching_config_type_1 = ContinuousBatchingConfig.from_dict(
                    data
                )

                return continuous_batching_config_type_1
            except:  # noqa: E722
                pass
            return cast(Union["ContinuousBatchingConfig", None, Unset], data)

        continuous_batching_config = _parse_continuous_batching_config(
            d.pop("continuous_batching_config", UNSET)
        )

        def _parse_dynamic_batching_config(
            data: object,
        ) -> Union["DynamicBatchingConfig", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                dynamic_batching_config_type_1 = DynamicBatchingConfig.from_dict(data)

                return dynamic_batching_config_type_1
            except:  # noqa: E722
                pass
            return cast(Union["DynamicBatchingConfig", None, Unset], data)

        dynamic_batching_config = _parse_dynamic_batching_config(
            d.pop("dynamic_batching_config", UNSET)
        )

        def _parse_filter_threshold(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        filter_threshold = _parse_filter_threshold(d.pop("filter_threshold", UNSET))

        def _parse_input_schema(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        input_schema = _parse_input_schema(d.pop("input_schema", UNSET))

        def _parse_openai(data: object) -> Union["OpenAiConfig", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                openai_type_1 = OpenAiConfig.from_dict(data)

                return openai_type_1
            except:  # noqa: E722
                pass
            return cast(Union["OpenAiConfig", None, Unset], data)

        openai = _parse_openai(d.pop("openai", UNSET))

        def _parse_output_schema(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        output_schema = _parse_output_schema(d.pop("output_schema", UNSET))

        def _parse_queue_depth(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        queue_depth = _parse_queue_depth(d.pop("queue_depth", UNSET))

        def _parse_sidekick_uri(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        sidekick_uri = _parse_sidekick_uri(d.pop("sidekick_uri", UNSET))

        def _parse_tensor_fields(data: object) -> Union[None, Unset, list[str]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tensor_fields_type_0 = cast(list[str], data)

                return tensor_fields_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[str]], data)

        tensor_fields = _parse_tensor_fields(d.pop("tensor_fields", UNSET))

        model_config_inner = cls(
            model_version_id=model_version_id,
            runtime=runtime,
            batch_config=batch_config,
            continuous_batching_config=continuous_batching_config,
            dynamic_batching_config=dynamic_batching_config,
            filter_threshold=filter_threshold,
            input_schema=input_schema,
            openai=openai,
            output_schema=output_schema,
            queue_depth=queue_depth,
            sidekick_uri=sidekick_uri,
            tensor_fields=tensor_fields,
        )

        model_config_inner.additional_properties = d
        return model_config_inner

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
