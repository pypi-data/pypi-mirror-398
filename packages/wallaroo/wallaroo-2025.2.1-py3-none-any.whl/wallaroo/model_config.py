from typing import TYPE_CHECKING, Any, Dict, List, cast

from .object import (
    DehydratedValue,
    Object,
    RequiredAttributeMissing,
    rehydrate,
    value_if_present,
)
from .openai_config import OpenaiConfig

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client
    from .model_version import ModelVersion


import gql  # type: ignore
import yaml


class ModelConfig(Object):
    """Wraps a backend ModelConfig object."""

    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
        self.client = client
        super().__init__(
            gql_client=client._gql_client if client is not None else None,
            data=data,
        )

    @property
    def inputs(self):
        return self.model_version().inputs

    @property
    def outputs(self):
        return self.model_version().outputs

    def to_k8s_yaml(self):
        # XXX - the deployment manager currently stitches this together
        extra = {
            "name": self.model_version().name(),
            "version": self.model_version().version(),
            "sha": self.model_version().sha(),
        }
        return self._yaml(extra)

    def _yaml(self, yaml_dict):
        if self.filter_threshold():
            yaml_dict["filter_threshold"] = self.filter_threshold()
        if self.runtime():
            yaml_dict["runtime"] = self.runtime()
        if self.tensor_fields():
            yaml_dict["tensor_fields"] = self.tensor_fields()
        if isinstance(self._input_schema, str):
            yaml_dict["input_schema"] = self._input_schema
        if isinstance(self._output_schema, str):
            yaml_dict["output_schema"] = self._output_schema
        if isinstance(self._batch_config, str):
            yaml_dict["batch_config"] = self._batch_config
        if self._dynamic_batching_config:
            yaml_dict["dynamic_batching_config"] = self.dynamic_batching_config()
        if self._openai_config:
            yaml_dict["openai_config"] = self.openai_config()
        return yaml.dump(yaml_dict)

    def _fill(self, data: Dict[str, Any]) -> None:
        """Fills an object given a response dictionary from the GraphQL API.

        Only the primary key member must be present; other members will be
        filled in via rehydration if their corresponding member function is
        called.
        """
        from .dynamic_batching_config import DynamicBatchingConfig
        from .model_version import ModelVersion  # Avoids circular imports

        for required_attribute in ["id"]:
            if required_attribute not in data:
                raise RequiredAttributeMissing(
                    self.__class__.__name__, required_attribute
                )
        # Required
        self._id = data["id"]

        # Optional
        self._filter_threshold = value_if_present(data, "filter_threshold")
        self._model_version = (
            (
                data["model"]
                if isinstance(data["model"], ModelVersion)
                else ModelVersion(
                    client=self.client,
                    data=data["model"],
                )
            )
            if "model" in data
            else DehydratedValue()
        )
        self._runtime = value_if_present(data, "runtime")
        self._tensor_fields = value_if_present(data, "tensor_fields")
        self._input_schema = value_if_present(data, "input_schema")
        self._output_schema = value_if_present(data, "output_schema")
        self._batch_config = value_if_present(data, "batch_config")
        self._dynamic_batching_config = (
            DynamicBatchingConfig.from_dict(data["dynamic_batching_config"])
            if "dynamic_batching_config" in data
            else DehydratedValue()
        )
        self._openai_config = (
            OpenaiConfig(**data["openai"]) if data.get("openai") is not None else None
        )

    def _fetch_attributes(self) -> Dict[str, Any]:
        """Fetches all member data from the GraphQL API."""
        assert self.client is not None
        return self.client._gql_client.execute(
            gql.gql(
                """
                query ModelConfigById($model_config_id: bigint!) {
                  model_config_by_pk(id: $model_config_id) {
                    id
                    filter_threshold
                    model {
                      id
                    }
                    runtime
                    tensor_fields
                    dynamic_batching_config
                    openai
                    input_schema
                    output_schema
                  }
                }
            """
            ),
            variable_values={
                "model_config_id": self._id,
            },
        )["model_config_by_pk"]

    def id(self) -> int:
        return self._id

    @rehydrate("_filter_threshold")
    def filter_threshold(self) -> float:
        return cast(float, self._filter_threshold)

    @rehydrate("_model_version")
    def model_version(self) -> "ModelVersion":
        from .model_version import ModelVersion  # Avoids circular imports

        return cast(ModelVersion, self._model_version)

    @rehydrate("_runtime")
    def runtime(self) -> str:
        return cast(str, self._runtime)

    @rehydrate("_tensor_fields")
    def tensor_fields(self) -> List[str]:
        return cast(List[str], self._tensor_fields)

    @rehydrate("_dynamic_batching_config")
    def dynamic_batching_config(self):
        from .dynamic_batching_config import DynamicBatchingConfig

        return cast(DynamicBatchingConfig, self._dynamic_batching_config)

    @rehydrate("_openai_config")
    def openai_config(self):
        from .openai_config import OpenaiConfig

        return cast(OpenaiConfig, self._openai_config)

    @rehydrate("_input_schema")
    def input_schema(self):
        return cast(str, self._input_schema)

    @rehydrate("_output_schema")
    def output_schema(self):
        return cast(str, self._output_schema)
