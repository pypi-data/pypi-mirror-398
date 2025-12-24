import base64
import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, cast

import gql  # type: ignore
import pandas as pd
import pyarrow as pa  # type: ignore
from dateutil import parser as dateparse

from wallaroo.exceptions import handle_errors
from wallaroo.utils import require_dns_compliance

from .continuous_batching_config import ContinuousBatchingConfig
from .deployment_config import DeploymentConfig, DeploymentConfigBuilder
from .dynamic_batching_config import DynamicBatchingConfig
from .engine_config import Acceleration, Architecture
from .object import (
    DehydratedValue,
    Object,
    RequiredAttributeMissing,
    rehydrate,
    value_if_present,
)
from .openai_config import OpenaiConfig
from .visibility import _Visibility

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client
    from .model_config import ModelConfig
    from .pipeline import Pipeline
    from .tag import Tag
    from .workspace import Workspace


# Wraps a backend model object.
class ModelVersion(Object):
    """The Wallaroo ModelVersion object. Each ModelVersion is a specific version of a Model."""

    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
        self.client = client
        self._config: Optional["ModelConfig"] = None
        self._wait_error: Optional[Exception] = None
        super().__init__(
            gql_client=client._gql_client if client is not None else None,
            data=data,
        )

    def __repr__(self) -> str:
        return str(
            {
                "name": self.name(),
                "version": self.version(),
                "file_name": self.file_name(),
                "image_path": self.image_path(),
                "arch": self.arch() or str(Architecture.default()),
                "accel": self.accel() or str(Acceleration.default()),
                "last_update_time": self.last_update_time(),
            }
        )

    def _repr_html_(self):
        self._rehydrate()
        fmt = self.client._time_format
        return f"""<table>
        <tr>
          <td>Name</td>
          <td>{self._name}</td>
        </tr>
        <tr>
          <td>Version</td>
          <td>{self._version}</td>
        </tr>
        <tr>
          <td>File Name</td>
          <td>{self._file_name}</td>
        </tr>
        <tr>
          <td>SHA</td>
          <td>{self._sha}</td>
        </tr>
        <tr>
          <td>Status</td>
          <td>{self._status}</td>
        </tr>
        <tr>
          <td>Image Path</td>
          <td>{self._image_path}</td>
        </tr>
        <tr>
          <td>Architecture</td>
          <td>{self._arch or Architecture.default()}</td>
        </tr>
        <tr>
          <td>Acceleration</td>
          <td>{self._accel or Acceleration.default()}</td>
        </tr>
        <tr>
          <td>Updated At</td>
          <td>{self._last_update_time.strftime(fmt)}</td>
        </tr>
        <tr>
          <td>Workspace id</td>
          <td>{self.workspace().id()}</td>
        </tr>
        <tr>
          <td>Workspace name</td>
          <td>{self.workspace().name()}</td>
        </tr>
      </table>"""

    def _fill(self, data: Dict[str, Any]) -> None:
        """Fills an object given a response dictionary from the GraphQL API.

        Only the primary key member must be present; other members will be
        filled in via rehydration if their corresponding member function is
        called.
        """
        from .tag import Tag
        from .workspace import Workspace

        for required_attribute in ["id"]:
            if required_attribute not in data:
                raise RequiredAttributeMissing(
                    self.__class__.__name__, required_attribute
                )
        # Required
        self._id = data["id"]

        # Optional
        self._name = value_if_present(data, "model_id")
        self._version = value_if_present(data, "model_version")
        self._models_pk_id = value_if_present(data, "models_pk_id")
        self._sha = value_if_present(data, "sha")
        self._status = value_if_present(data, "status")
        self._file_name = value_if_present(data, "file_name")
        self._image_path = value_if_present(data, "image_path")
        self._arch = value_if_present(data, "arch")
        self._accel = value_if_present(data, "accel")
        self._last_update_time = (
            dateparse.isoparse(data["updated_at"])
            if "updated_at" in data
            else DehydratedValue()
        )
        self._visibility = (
            _Visibility.from_str(data["visibility"])
            if "visibility" in data
            else DehydratedValue()
        )
        self._tags = (
            [Tag(self.client, tag["tag"]) for tag in data["model_tags"]]
            if "model_tags" in data
            else DehydratedValue()
        )
        self._workspace = (
            Workspace(self.client, data["model"]["workspace"])
            if "model" in data and "workspace" in data["model"]
            else DehydratedValue()
        )

    def _fetch_attributes(self) -> Dict[str, Any]:
        """Fetches all member data from the GraphQL API."""
        return self._gql_client.execute(
            gql.gql(
                f"""
            query ModelById {{
                model_by_pk(id: {self._id}) {{
                    id
                    created_on_version
                    model_id
                    model_version
                    models_pk_id    
                    sha
                    status
                    file_name
                    image_path
                    updated_at
                    visibility
                    model_tags {{
                      tag {{
                        id
                        tag
                      }}
                    }}
                    arch: conversion(path: "arch")
                    accel: conversion(path: "accel")
                    model{{
                        workspace {{
                            id
                            name
                        }}
                    }}
                }}
            }}
            """
            )
        )["model_by_pk"]

    def id(self) -> int:
        return self._id

    def uid(self) -> str:
        return f"{self.name()}-{self.id()}"

    @rehydrate("_name")
    def name(self) -> str:
        return cast(str, self._name)

    @rehydrate("_version")
    def version(self) -> str:
        return cast(str, self._version)

    # TODO: Find other models by finding the parent?
    # @rehydrate("_versions")
    # def versions(self) -> "Models":
    #     from .models import Models

    #     return Models(client=self.client, data={"id": self._models_pk_id})

    @rehydrate("_models_pk_id")
    def models_pk_id(self) -> str:
        return cast(str, self._models_pk_id)

    @rehydrate("_sha")
    def sha(self) -> str:
        return cast(str, self._sha)

    @rehydrate("_status")
    def status(self) -> str:
        self._rehydrate()
        return cast(str, self._status)

    @rehydrate("_file_name")
    def file_name(self) -> str:
        return cast(str, self._file_name)

    @rehydrate("_image_path")
    def image_path(self) -> str:
        return cast(str, self._image_path)

    @rehydrate("_arch")
    def arch(self) -> str:
        return cast(str, self._arch)

    @rehydrate("_accel")
    def accel(self) -> str:
        return cast(str, self._accel)

    @rehydrate("_last_update_time")
    def last_update_time(self) -> datetime.datetime:
        return cast(datetime.datetime, self._last_update_time)

    @rehydrate("_tags")
    def tags(self) -> List["Tag"]:
        from .tag import Tag  # avoids import cycles

        return cast(List[Tag], self._tags)

    @rehydrate("_workspace")
    def workspace(self) -> "Workspace":
        from .workspace import Workspace

        return cast(Workspace, self._workspace)

    @rehydrate("_config")
    def rehydrate_config(self) -> "ModelConfig":
        from .model_config import ModelConfig

        if self._config is not None:
            return self._config
        if self.client is None:
            raise Exception("Cannot retrieve current model config, client is None.")
        assert self.client is not None
        raw = self.client.httpx_client.post(
            "v1/api/models/get_config_by_id",
            json={"model_id": self.id()},
        )
        if raw.status_code > 299:
            raise Exception(
                "Failed to retrieve config from api, and failed to automatically configure model."
            )
        possible_model_config = raw.json()
        if possible_model_config["model_config"]:
            return ModelConfig(
                client=self.client, data=possible_model_config["model_config"]
            )
        else:
            raise Exception(
                "Failed to determine model configuration, could not auto configure based on name, and no existing "
                "model configuration was present. "
            )

    def _update_visibility(self, visibility: _Visibility):
        assert self.client is not None
        return self._fill(
            self.client._gql_client.execute(
                gql.gql(
                    """
                mutation UpdateModelVisibility(
                    $model_pk: bigint!,
                    $visibility: String
                ) {
                  update_model(where: {id: {_eq: $model_pk}}, _set: {visibility: $visibility}) {
                        returning {
                          id
                          model_id
                          model_version
                          file_name
                          visibility
                          updated_at
                        }
                    }
                }
                """
                ),
                variable_values={
                    "model_pk": self._id,
                    "visibility": visibility,
                },
            )["update_model"]["returning"][0]
        )

    def config(self) -> "ModelConfig":
        if self._config is None:
            try:
                self._config = self.rehydrate_config()
            except Exception:
                self.configure()
        assert self._config is not None
        return cast("ModelConfig", self._config)

    def configure(
        self,
        runtime: Optional[str] = None,
        tensor_fields: Optional[List[str]] = None,
        filter_threshold: Optional[float] = None,
        input_schema: Optional[pa.Schema] = None,
        output_schema: Optional[pa.Schema] = None,
        batch_config: Optional[str] = None,
        dynamic_batching_config: Optional[DynamicBatchingConfig] = None,
        continuous_batching_config: Optional[ContinuousBatchingConfig] = None,
        openai_config: Optional[OpenaiConfig] = None,
    ) -> "ModelVersion":
        self._validate_dynamic_batching_config(batch_config, dynamic_batching_config)
        self._validate_continuous_batching_config(
            batch_config, continuous_batching_config
        )
        return self._configure_via_models(
            tensor_fields,
            filter_threshold,
            input_schema,
            output_schema,
            batch_config,
            dynamic_batching_config,
            continuous_batching_config,
            openai_config,
        )

    @handle_errors()
    def _configure_via_models(
        self,
        tensor_fields: Optional[List[str]] = None,
        filter_threshold: Optional[float] = None,
        input_schema: Optional[pa.Schema] = None,
        output_schema: Optional[pa.Schema] = None,
        batch_config: Optional[str] = None,
        dynamic_batching_config: Optional[DynamicBatchingConfig] = None,
        continuous_batching_config: Optional[ContinuousBatchingConfig] = None,
        openai_config: Optional[OpenaiConfig] = None,
    ) -> "ModelVersion":
        from .model_config import ModelConfig  # Avoids circular imports

        request: Dict[str, Any] = {"model_version_id": self.id()}

        if tensor_fields:
            request["tensor_fields"] = tensor_fields
        if filter_threshold:
            request["filter_threshold"] = filter_threshold
        if input_schema:
            request["input_schema"] = base64.b64encode(
                bytes(input_schema.serialize())
            ).decode("utf8")
        if output_schema:
            request["output_schema"] = base64.b64encode(
                bytes(output_schema.serialize())
            ).decode("utf8")
        if batch_config:
            request["batch_config"] = batch_config

        if dynamic_batching_config:
            request["dynamic_batching_config"] = dynamic_batching_config.to_json()

        if continuous_batching_config:
            request["continuous_batching_config"] = (
                continuous_batching_config.model_dump()
            )
        if openai_config:
            request["openai_config"] = openai_config.model_dump()

        assert self.client is not None
        raw = self.client.httpx_client.post(
            "v1/api/models/insert_model_config",
            json=request,
        )
        raw.raise_for_status()

        possible_model_config = raw.json()
        if possible_model_config["model_config"]:
            self._config = ModelConfig(
                client=self.client,
                data=possible_model_config["model_config"],
            )
            self._config._model_version = self
            return self
        else:
            raise Exception(
                "Failed to determine model configuration, could not auto configure based on name, and no existing "
                "model configuration was present. "
            )

    def logs(
        self,
        limit: int = 100,
        valid: Optional[bool] = None,
        arrow: Optional[bool] = False,
    ) -> Tuple[Any, Union[str, None]]:
        topic = f"model-{self.name()}-inference"
        if valid is False:
            topic += "-failures"
        assert self.client is not None
        logs = self.client.get_logs(topic, limit, arrow=arrow)
        return logs if isinstance(logs, (pa.Table, pd.DataFrame)) else logs[0]

    def deploy(
        self,
        pipeline_name: str,
        deployment_config: Optional[DeploymentConfig] = None,
    ) -> "Pipeline":
        """Convenience function to quickly deploy a Model. It will configure the model,
        create a pipeline with a single model step, deploy it, and return the pipeline.

        Typically, the configure() method is used to configure a model prior to
        deploying it. However, if a default configuration is sufficient, this
        function can be used to quickly deploy with said default configuration.

        The filename this Model was generated from needs to have a recognizable
        file extension so that the runtime can be inferred. Currently, this is:

        * `.onnx` -> ONNX runtime

        :param str deployment_name: Name of the deployment to create. Must be
            unique across all deployments. Deployment names must be ASCII alpha-numeric
            characters plus dash (-) only.

        """

        assert self.client is not None

        require_dns_compliance(pipeline_name)

        workspace_id = (
            None if self.client is None else self.client.get_current_workspace().id()
        )

        if deployment_config is None:
            deployment_config = DeploymentConfigBuilder(
                workspace_id=workspace_id
            ).build()
        else:
            deployment_config._guarantee_workspace_id(workspace_id=workspace_id)

        pipeline = self.client.build_pipeline(pipeline_name)

        pipeline.add_model_step(self)

        pipeline.deploy(pipeline_name, deployment_config=deployment_config)

        return pipeline

        # TODO - wait_for_running

    def _validate_dynamic_batching_config(
        self,
        batch_config: Optional[str],
        dynamic_batching_config: Optional[DynamicBatchingConfig],
    ) -> None:
        if batch_config == "single" and dynamic_batching_config is not None:
            raise ValueError(
                "Dynamic batching is not supported with single batch mode. "
                "Please update the model configuration or contact Wallaroo for support at support@wallaroo.ai"
            )

    def _validate_continuous_batching_config(
        self,
        batch_config: Optional[str],
        continuous_batching_config: Optional[ContinuousBatchingConfig],
    ) -> None:
        if batch_config is not None and continuous_batching_config is not None:
            raise ValueError(
                "Continuous batching is not supported when setting batch_config."
                "Please update the model configuration or contact wallaroo for support at support@wallaroo.ai"
            )


class ModelVersionList(List[ModelVersion]):
    """Wraps a list of model versions for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(model: ModelVersion):
            return f"""
            <tr>
                <td>{model.name()}</td>
                <td>{model.version()}</td>
                <td>{model.file_name()}</td>
                <td>{model.image_path()}</td>
                <td>{model.arch() or str(Architecture.default())}</td>
                <td>{model.accel() or str(Acceleration.default())}</td>
                <td>{model.last_update_time()}</td>
                <td>{model.workspace().id()}</td>
                <td>{model.workspace().name()}</td>
            </tr>
          """

        fields = [
            "name",
            "version",
            "file_name",
            "image_path",
            "arch",
            "accel",
            "last_update_time",
            "workspace_id",
            "workspace_name",
        ]
        if not self:
            return "(no model versions)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(m) for m in self]))
                + "</table>"
            )
