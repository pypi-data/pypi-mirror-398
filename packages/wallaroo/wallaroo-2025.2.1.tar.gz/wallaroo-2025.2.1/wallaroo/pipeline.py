import asyncio
import datetime
import math
import os
import pathlib
import sys
import time
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

import httpx
import numpy as np
import pandas as pd
import polars
import pyarrow as pa  # type: ignore
from dateutil import parser as dateparse
from httpx import AsyncClient
from openai import OpenAI

from wallaroo.utils import require_dns_compliance

from . import queries
from .deployment import Deployment
from .deployment_config import DeploymentConfig
from .edge import Edge, EdgeList
from .engine_config import Acceleration, Architecture
from .model_config import ModelConfig
from .model_version import ModelVersion
from .object import (
    DehydratedValue,
    EntityNotFoundError,
    Object,
    RequiredAttributeMissing,
    gql,
    rehydrate,
    value_if_present,
)
from .openapi_tmpl import (
    DEFAULT_SCHEMA,
    WITH_OPENAI,
    WITHOUT_OPENAI,
    arrow_schema_to_openapi_yaml,
    decode_arrow_schema_from_base64,
)
from .pipeline_config import PipelineConfigBuilder, Step
from .pipeline_publish import PipelinePublish, PipelinePublishList
from .visibility import _Visibility
from .wallaroo_ml_ops_api_client.api.pipelines import pipelines_get_version
from .wallaroo_ml_ops_api_client.models import (
    PipelinesGetVersionResponse200,
    pipelines_get_version_body,
)

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client
    from .deployment import Deployment
    from .pipeline_version import PipelineVersion
    from .tag import Tag
    from .workspace import Workspace

DEFAULT_LOGS_DIRECTORY = "logs"


def update_timestamp(f):
    def _inner(self, *args, **kwargs):
        results = f(self, *args, **kwargs)
        if isinstance(results, list):
            # TODO do we still allow arbitrary json?
            # could be arbitrary json, which may not have "time" in results.
            self._last_infer_time = None
        elif isinstance(results, pd.DataFrame):
            if "time" in results:
                self._last_infer_time = results["time"].max()
        elif isinstance(results, pa.Table):
            if "time" in results:
                min_max_time = pa.compute.min_max(results["time"])
                self._last_infer_time = min_max_time["max"].as_py()

        return results

    return _inner


def _accel_from_deployment(deployment: Deployment) -> str:
    accel = str(Acceleration._None)
    engine_aux_images = (
        deployment.engine_config().get("engineAux", dict()).get("images", dict())
    )
    # find the first non-none accel that's specified anywhere in the engineAux.images
    if engine_aux_images:
        non_none_accels = [
            img.get("accel", str(Acceleration.default()))
            for img in engine_aux_images.values()
            if img.get("accel", str(Acceleration.default())) != str(Acceleration._None)
        ]

        # If there's only one non-none accel, use it. Else, leave it as none.
        if len(set(non_none_accels)) == 1:
            accel = non_none_accels[0]
    return accel


def _accel_from_model_configs(model_configs: List[ModelConfig]) -> str:
    accel = str(Acceleration._None)
    if model_configs:
        # Get all non-none accelerations from model configs
        non_none_accels = [
            mc.model_version().accel()
            for mc in model_configs
            if mc.model_version().accel() != Acceleration._None
        ]

        # If there's only one non-none accel, use it. Else, leave it as none.
        if len(set(non_none_accels)) == 1:
            accel = non_none_accels[0]
        else:
            accel = str(Acceleration._None)
    return accel


def _accel_from_deployment_or_model_configs(
    deployment: Optional[Deployment], model_configs: List[ModelConfig]
) -> str:
    # If pipeline is deployed, but accel is none, try to find the accel from the engineAux.images.
    if deployment is not None:
        accel = (
            deployment.engine_config()
            .get("engine", dict())
            .get("accel", str(Acceleration.default()))
        )
        if accel == Acceleration._None:
            accel = _accel_from_deployment(deployment)

    # if pipeline is not deployed, use the accel from the model configs.
    if deployment is None:
        accel = _accel_from_model_configs(model_configs)
    return accel


class Pipeline(Object):
    """A pipeline is an execution context for models.
    Pipelines contain Steps, which are often Models.
    Pipelines can be deployed or un-deployed."""

    def __init__(
        self,
        client: "Client",
        data: Dict[str, Any],
    ) -> None:
        self.client = client
        assert client is not None

        # We track the last timestamp received as a hack, so that we can wait for logs
        # that are still being processed.
        self._last_infer_time = None

        # We will shim through to all builder methods but return self so we can chain pipeline
        # calls. See "Shims" below. Using multiple inheritance from the PipelineConfigBuilder was
        # another option considered, and maybe it's an option, but shims let us fiddle with args
        # individually if needed.
        self._builder = None
        self._deployment = None
        self._pipeline_version_to_deploy = None

        super().__init__(gql_client=client._gql_client, data=data)

    def __repr__(self) -> str:
        return str(
            {
                "name": self.name(),
                "create_time": self.create_time(),
                "definition": self.definition(),
            }
        )

    def _html_steptable(self) -> str:
        models = self._fetch_models()
        return ", ".join(models)

        # Yes this is biased towards models only
        # TODO: other types of steps
        # steps = self.steps()
        # steptable = ""
        # if steps:
        #     rows = ""
        #     for step in steps:
        #         rows += step._repr_html_()
        #     steptable = f"<table>{rows}</table>"
        # else:
        #     steptable = "(no steps)"
        # return steptable

    def _repr_html_(self) -> str:
        tags = ", ".join([tag.tag() for tag in self.tags()])
        deployment = self._deployment_for_pipeline()
        deployed = "(none)" if deployment is None else deployment.deployed()
        arch = (
            None
            if deployment is None
            else deployment.engine_config()
            .get("engine", dict())
            .get("arch", str(Architecture.default()))
        )
        accel = _accel_from_deployment_or_model_configs(
            deployment, self.model_configs()
        )

        versions = ", ".join([version.name() for version in self.versions()])

        return (
            f"<table>"
            f"<tr><th>name</th> <td>{self.name()}</td></tr>"
            f"<tr><th>created</th> <td>{self.create_time()}</td></tr>"
            f"<tr><th>last_updated</th> <td>{self.last_update_time()}</td></tr>"
            f"<tr><th>deployed</th> <td>{deployed}</td></tr>"
            f"<tr><th>workspace_id</th> <td>{self.workspace().id()}</td></tr>"
            f"<tr><th>workspace_name</th> <td>{self.workspace().name()}</td></tr>"
            f"<tr><th>arch</th> <td>{arch}</td></tr>"
            f"<tr><th>accel</th> <td>{accel}</td></tr>"
            f"<tr><th>tags</th> <td>{tags}</td></tr>"
            f"<tr><th>versions</th> <td>{versions}</td></tr>"
            f"<tr><th>steps</th> <td>{self._html_steptable()}</td></tr>"
            f"<tr><th>published</th> <td>{True if any([len(version._publishes) > 0 for version in self.versions()]) > 0 else False}</td></tr>"
            f"</table>"
        )

    def _is_named(self) -> bool:
        try:
            self.name()
            return True
        except Exception:
            return False

    def builder(self) -> "PipelineConfigBuilder":
        if self._builder is None:
            self._builder = PipelineConfigBuilder(
                self.client,
                pipeline_name=self.name(),
            )
        return cast(PipelineConfigBuilder, self._builder)

    def _fill(self, data: Dict[str, Any]) -> None:
        from .pipeline_version import PipelineVersion  # avoids circular imports
        from .tag import Tag
        from .workspace import Workspace

        for required_attribute in ["id"]:
            if required_attribute not in data:
                raise RequiredAttributeMissing(
                    self.__class__.__name__, required_attribute
                )
        self._id = data["id"]

        # Optional
        self._owner_id = value_if_present(data, "owner_id")

        # Optional
        self._tags = (
            [Tag(self.client, tag["tag"]) for tag in data["pipeline_tags"]]
            if "pipeline_tags" in data
            else DehydratedValue()
        )
        self._create_time = (
            dateparse.isoparse(data["created_at"])
            if "created_at" in data
            else DehydratedValue()
        )
        self._last_update_time = (
            dateparse.isoparse(data["updated_at"])
            if "updated_at" in data
            else DehydratedValue()
        )
        self._name = value_if_present(data, "pipeline_id")
        self._versions = (
            [PipelineVersion(self.client, elem) for elem in data["pipeline_versions"]]
            if "pipeline_versions" in data
            else DehydratedValue()
        )
        self._workspace = (
            Workspace(self.client, data["workspace"])
            if "workspace" in data
            else DehydratedValue()
        )

    def _fetch_attributes(self) -> Dict[str, Any]:
        assert self.client is not None
        return self.client._gql_client.execute(
            gql.gql(
                """
            query PipelineById($pipeline_id: bigint!) {
                pipeline_by_pk(id: $pipeline_id) {
                    id
                    pipeline_id
                    created_at
                    updated_at
                    visibility
                    owner_id
                    pipeline_versions(order_by: {id: desc}) {
                        id
                        pipeline_publishes {
                          created_on_version
                          chart_url
                          engine_url
                          engine_config
                          id
                          pipeline_url
                          pipeline_version_id
                          status
                          updated_at
                          created_by
                          created_at
                          user_images
                        }
                    }
                    pipeline_tags {
                      tag {
                        id
                        tag
                      }
                    }
                    workspace {
                        id
                        name
                    }
                }
            }
                """
            ),
            variable_values={
                "pipeline_id": self._id,
            },
        )["pipeline_by_pk"]

    def _update_visibility(self, visibility: _Visibility):
        assert self.client is not None
        return self._fill(
            self.client._gql_client.execute(
                gql.gql(
                    """
                mutation UpdatePipelineVisibility(
                    $pipeline_id: bigint!,
                    $visibility: String
                ) {
                  update_pipeline(
                    where: {id: {_eq: $pipeline_id}},
                    _set: {visibility: $visibility}) {
                      returning  {
                          id
                          pipeline_id
                          created_at
                          updated_at
                          visibility
                          owner_id
                          pipeline_versions(order_by: {id: desc}) {
                                id
                            }
                        }
                    }
                }
                """
                ),
                variable_values={
                    "pipeline_id": self._id,
                    "visibility": visibility,
                },
            )["update_pipeline"]["returning"][0]
        )

    def _fetch_models(self):
        """Load deployment and any models associated, used only for listing and searching cases."""
        data = self._gql_client.execute(
            gql.gql(queries.named("PipelineModels")),
            variable_values={"pipeline_id": self.id()},
        )
        names = []
        try:
            mc_nodes = data["pipeline_by_pk"]["deployment"][
                "deployment_model_configs_aggregate"
            ]["nodes"]
            names = [mc["model_config"]["model"]["model"]["name"] for mc in mc_nodes]
        except Exception:
            pass
        return names

    def id(self) -> int:
        return self._id

    @rehydrate("_owner_id")
    def owner_id(self) -> str:
        return cast(str, self._owner_id)

    @rehydrate("_create_time")
    def create_time(self) -> datetime.datetime:
        return cast(datetime.datetime, self._create_time)

    @rehydrate("_last_update_time")
    def last_update_time(self) -> datetime.datetime:
        return cast(datetime.datetime, self._last_update_time)

    @rehydrate("_name")
    def name(self) -> str:
        return cast(str, self._name)

    @rehydrate("_versions")
    def versions(self) -> List["PipelineVersion"]:
        from .pipeline_version import PipelineVersion  # avoids import cycles

        return cast(List[PipelineVersion], self._versions)

    @rehydrate("_tags")
    def tags(self) -> List["Tag"]:
        from .tag import Tag

        return cast(List[Tag], self._tags)

    @rehydrate("_workspace")
    def workspace(self) -> "Workspace":
        from .workspace import Workspace

        return cast(Workspace, self._workspace)

    def get_pipeline_configuration(
        self, version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a pipeline configuration for a specific version.
        :param version: str Version of the pipeline.
        :return Dict[str, Any] Pipeline configuration.
        """
        assert self.client is not None
        # if version not provided, use the latest pipeline version available
        if version is None:
            version = self.versions()[0].name()
        data = pipelines_get_version.sync(
            client=self.client.mlops(),
            body=pipelines_get_version_body.PipelinesGetVersionBody.from_dict(
                {"version": version}
            ),
        )
        if data is None:
            raise Exception("Failed to get pipeline version")
        if not isinstance(data, PipelinesGetVersionResponse200):
            raise Exception(data.msg)
        # TODO: Get pipeline version id and return PipelineVersion?
        return data.to_dict()

    @staticmethod
    def _write_metadata_warning(log_table):
        if "metadata.dropped" in log_table.column_names:
            flattened_metadata = log_table["metadata.dropped"].flatten()
            if len(flattened_metadata[0][0]) > 0:
                dropped_columns = flattened_metadata[0][0]
                sys.stderr.write(
                    f"Warning: The inference log is above the allowable limit and the following columns may have"
                    f" been suppressed for various rows in the logs: {dropped_columns}."
                    f" To review the dropped columns for an individual inference’s suppressed data,"
                    f' include dataset=["metadata"] in the log request.'
                    f"\n"
                )

    @staticmethod
    def _drop_metadata_columns(dataset, log_table):
        columns_to_drop = []
        if dataset is None or "metadata" not in dataset:
            for column_name in log_table.column_names:
                if column_name.startswith("metadata"):
                    columns_to_drop.append(column_name)
        return log_table.drop(columns_to_drop)

    def logs(
        self,
        limit: Optional[int] = None,
        start_datetime: Optional[datetime.datetime] = None,
        end_datetime: Optional[datetime.datetime] = None,
        valid: Optional[bool] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
        arrow: Optional[bool] = False,
    ) -> Union[pa.Table, pd.DataFrame]:
        """
        Get inference logs for this pipeline.
        :param limit: Optional[int]: Maximum number of logs to return.
        :param start_datetime: Optional[datetime.datetime]: Start time for logs.
        :param end_datetime: Optional[datetime.datetime]: End time for logs.
        :param valid: Optional[bool]: If set to False, will include logs for failed inferences
        :param dataset: Optional[List[str]] By default this is set to ["*"] which returns,
            ["time", "in", "out", "anomaly"]. Other available options - ["metadata"]
        :param dataset_exclude: Optional[List[str]] If set, allows user to exclude parts of dataset.
        :param dataset_separator: Optional[Union[Sequence[str], str]] If set to ".", return dataset will be flattened.
        :param arrow: Optional[bool] If set to True, return logs as an Arrow Table. Else, returns Pandas DataFrame.
        :return: Union[pa.Table, pd.DataFrame]
        """
        topic = self.get_topic_name()

        if valid is False:
            topic += "-failures"
        assert self.client is not None
        entries, status = self.client.get_logs(
            topic,
            limit,
            start_datetime,
            end_datetime,
            dataset,
            dataset_exclude,
            dataset_separator,
            arrow=True,
        )
        # XXX: hack to attempt to align logs with received inference results.
        # Ideally we'd use indices from plateau directly for querying, but the
        # engine currently does not support that.
        if self._last_infer_time is not None:
            for ix in range(5):
                if (
                    entries
                    and self._last_infer_time
                    <= pa.compute.min_max(entries["time"])["max"].as_py()
                ):
                    break

                time.sleep(1)
                entries, status = self.client.get_logs(
                    topic,
                    limit,
                    start_datetime,
                    end_datetime,
                    dataset,
                    dataset_exclude,
                    dataset_separator,
                    arrow=True,
                )

        if status == "SchemaChange":
            chronological_order = (
                "oldest"
                if start_datetime is not None and end_datetime is not None
                else "newest"
            )
            assert entries is not None
            sys.stderr.write(
                f"Pipeline log schema has changed over the logs requested {entries.num_rows}"
                f" {chronological_order} records retrieved successfully, {chronological_order}"
                f" record seen was at <datetime>. Please request additional records separately"
                f"\n"
            )

        self._write_metadata_warning(entries)
        entries = self._drop_metadata_columns(dataset, entries)
        if not arrow:
            entries = entries.to_pandas()

        if status == "ByteLimited":
            sys.stderr.write(
                "Warning: Pipeline log size limit exceeded. Please request logs using export_logs",
            )
        elif status == "RecordLimited":
            sys.stderr.write(
                "Warning: There are more logs available. "
                "Please set a larger limit or request a file using export_logs."
            )
        return entries

    def export_logs(
        self,
        directory: Optional[str] = None,
        file_prefix: Optional[str] = None,
        data_size_limit: Optional[str] = None,
        limit: Optional[int] = None,
        start_datetime: Optional[datetime.datetime] = None,
        end_datetime: Optional[datetime.datetime] = None,
        valid: Optional[bool] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
        arrow: Optional[bool] = False,
    ) -> None:
        """
        Export logs to a user provided local file.
        :param directory: Optional[str] Logs will be exported to a file in the given directory.
            By default, logs will be exported to new "logs" subdirectory in current working directory.
        :param file_prefix: Optional[str] Prefix to name the exported file. By default, the file_prefix will be set to
            the pipeline name.
        :param data_size_limit: Optional[str] The maximum size of the exported data in bytes.
            Size includes all files within the provided directory. By default, the data_size_limit will be set to 100MB.
        :param limit: Optional[int] The maximum number of logs to return.
        :param start_datetime: Optional[datetime.datetime] The start time to filter logs by.
        :param end_datetime: Optional[datetime.datetime] The end time to filter logs by.
        :param valid: Optional[bool] If set to False, will return logs for failed inferences.
        :param dataset: Optional[List[str]] By default this is set to ["*"] which returns,
            ["time", "in", "out", "anomaly"]. Other available options - ["metadata"]
        :param dataset_exclude: Optional[List[str]] If set, allows user to exclude parts of dataset.
        :param dataset_separator: Optional[Union[Sequence[str], str]] If set to ".", return dataset will be flattened.
        :param arrow: Optional[bool] If set to True, return logs as an Arrow Table. Else, returns Pandas DataFrame.
        :return None
        """
        topic = self.get_topic_name()

        if valid is False:
            topic += "-failures"
        assert self.client is not None

        if directory is None:
            directory = DEFAULT_LOGS_DIRECTORY
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                raise Exception(f"Error while creating directory: {e}")
        if file_prefix is None:
            file_prefix = self.name()

        self.client.get_logs(
            topic=topic,
            limit=limit,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            dataset=dataset,
            dataset_exclude=dataset_exclude,
            dataset_separator=dataset_separator,
            directory=directory,
            file_prefix=file_prefix,
            data_size_limit=data_size_limit,
            arrow=arrow,
        )

    def url(self) -> str:
        """Returns the inference URL for this pipeline."""
        deployment = self._deployment_for_pipeline()
        if deployment is None:
            raise RuntimeError("Pipeline has not been deployed and has no url")
        else:
            return deployment.url()

    def deploy(
        self,
        pipeline_name: Optional[str] = None,
        deployment_config: Optional[DeploymentConfig] = None,
        wait_for_status: Optional[bool] = True,
    ) -> Union[None, "Pipeline"]:
        """Deploy pipeline. `pipeline_name` is optional if deploy was called previously. When specified,
        `pipeline_name` must be ASCII alpha-numeric characters, plus dash (-) only.

        :param pipeline_name: Optional[str] Name of the pipeline to deploy.
        :param deployment_config: Optional[DeploymentConfig] Deployment configuration.
        :param wait_for_status: If set to False, will not wait for deployment status.
            If set to True, will wait for deployment status to be running or encountered an error.
            Default is True.

        :return: Pipeline
        """
        if pipeline_name is not None:
            require_dns_compliance(pipeline_name)
        self._deploy_upload_optional(
            pipeline_name=pipeline_name,
            deployment_config=deployment_config,
            wait_for_status=wait_for_status,
        )
        return self

    def definition(self) -> str:
        """Get the current definition of the pipeline as a string"""
        return str(self.builder().steps)

    def _deploy_upload_optional(
        self,
        pipeline_name: Optional[str] = None,
        deployment_config: Optional[DeploymentConfig] = None,
        wait_for_status: Optional[bool] = True,
        upload: bool = True,
    ) -> Union[None, "Pipeline"]:
        """INTERNAL USE ONLY: This is used in convenience methods that create pipelines"""

        if pipeline_name is None:
            if not self._is_named():
                raise RuntimeError(
                    "pipeline_name is required when pipeline was not previously deployed."
                )
            else:
                pipeline_name = self.name()
        if upload:
            self._upload()

        self._deployment = self.versions()[0].deploy(
            deployment_name=pipeline_name,
            model_configs=self.builder()._model_configs(),
            config=deployment_config,
            wait_for_status=wait_for_status,
        )
        # we've already created new version based off this one and deployed it, so no need to keep track.
        self._pipeline_version_to_deploy = None
        return self

    def _deployment_for_pipeline(
        self, is_async: Optional[bool] = False
    ) -> Optional["Deployment"]:
        """Fetch a pipeline's deployment."""
        if self._deployment is not None:
            if not isinstance(self._deployment, DehydratedValue) and not is_async:
                self._deployment._rehydrate()
            return self._deployment

        res = self._gql_client.execute(
            gql.gql(
                """
		query GetDeploymentForPipeline($pipeline_id: bigint!) {
		  pipeline_by_pk(id: $pipeline_id) {
		    deployment {
		      id
		      deploy_id
		      deployed
              engine_config
		    }
		  }
		}"""
            ),
            variable_values={
                "pipeline_id": self.id(),
            },
        )
        if not res["pipeline_by_pk"]:
            raise EntityNotFoundError("Pipeline", {"pipeline_id": str(self.id())})

        if res["pipeline_by_pk"]["deployment"]:
            self._deployment = Deployment(
                client=self.client,
                data=res["pipeline_by_pk"]["deployment"],
            )
        return self._deployment

    def get_topic_name(self) -> str:
        if self.client is None:
            return f"pipeline-{self.name()}-inference"
        return self.client.get_topic_name(self.id())

    # -----------------------------------------------------------------------------
    # Shims for Deployment methods
    # -----------------------------------------------------------------------------

    def undeploy(self) -> "Pipeline":
        assert self.client is not None
        deployment = self._deployment_for_pipeline()
        if deployment:
            deployment.undeploy()
        return self

    @update_timestamp
    def infer(
        self,
        tensor: Union[Dict[str, Any], pd.DataFrame, pa.Table],
        timeout: Optional[Union[int, float]] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
    ) -> Union[pd.DataFrame, pa.Table]:
        """
        Inferences are performed on deployed pipelines. A pipeline processes data sequentially
        through a series of steps, where each step's output becomes the input for the next step.
        The final output represents the result of the entire pipeline's processing.

        :param: tensor: Union[Dict[str, Any], pd.DataFrame, pa.Table] The data submitted to the pipeline for inference.
        :param: timeout: Optional[Union[int, float]] infer requests will time out after
            the amount of seconds provided are exceeded. timeout defaults
            to 15 secs.
        :param: dataset: Optional[List[str]] By default this is set to ["*"] which returns,
            ["time", "in", "out", "anomaly"]. Other available options - ["metadata"]
        :param: dataset_exclude: Optional[List[str]] If set, allows user to exclude parts of dataset.
        :param: dataset_separator: Optional[Union[Sequence[str], str]] If set to ".", return dataset will be flattened.
        :return: DataFrame or Arrow format.
        """
        deployment = self._deployment_for_pipeline()
        if deployment:
            return deployment.infer(
                tensor, timeout, dataset, dataset_exclude, dataset_separator
            )
        else:
            raise RuntimeError("Pipeline {self.name} is not deployed")

    @update_timestamp
    def infer_from_file(
        self,
        filename: Union[str, pathlib.Path],
        data_format: Optional[str] = None,
        timeout: Optional[Union[int, float]] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
    ) -> Union[pd.DataFrame, pa.Table]:
        """
        This method is used to run inference on a deployment using a file. The file can be in one of the following
        formats: pandas.DataFrame: .arrow, .json which contains data either in the pandas.records format
        or wallaroo custom json format.
        :param: filename: Union[str, pathlib.Path]. The file to be sent to run inference on.
        :param: data_format: Optional[str]. The format of the data in the file. If not provided, the format will be
            inferred from the file extension.
        :param: timeout: Optional[Union[int, float]] infer requests will time out after the amount of seconds provided are
            exceeded. timeout defaults to 15 secs.
        :param: dataset: Optional[List[str]] By default this is set to ["*"] which returns,
            ["time", "in", "out", "anomaly"]. Other available options - ["metadata"]
        :param: dataset_exclude: Optional[List[str]] If set, allows user to exclude parts of dataset.
        :param: dataset_separator: Optional[str] If set to ".", returned dataset will be flattened.
        :return: Inference result in the form of pd.DataFrame, pa.Table, dict or list.
        """

        deployment = self._deployment_for_pipeline()
        if deployment:
            return deployment.infer_from_file(
                filename,
                data_format,
                timeout,
                dataset,
                dataset_exclude,
                dataset_separator,
            )
        else:
            raise RuntimeError("Pipeline {self.name} is not deployed")

    async def async_infer(
        self,
        tensor: Union[Dict[str, Any], pd.DataFrame, pa.Table],
        async_client: AsyncClient,
        timeout: Optional[Union[int, float]] = None,
        retries: Optional[int] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
    ):
        """
        Runs an async inference and returns an inference result on this deployment, given a tensor.
        :param: tensor: Union[Dict[str, Any], pd.DataFrame, pa.Table] Inference data.
        :param: async_client: AsyncClient Async client to use for async inference.
        :param: timeout: Optional[Union[int, float]] infer requests will time out after
            the amount of seconds provided are exceeded. timeout defaults
            to 15 secs.
        :param: retries: Optional[int] Number of retries to use in case of Connection errors.
        :param: job_id: Optional[int] Job id to use for async inference.
        :param: dataset: Optional[List[str]] By default this is set to ["*"] which returns,
            ["time", "in", "out", "anomaly"]. Other available options - ["metadata"]
        :param: dataset_exclude: Optional[List[str]] If set, allows user to exclude parts of dataset.
        :param: dataset_separator: Optional[Union[Sequence[str], str]] If set to ".", return dataset will be flattened.
        """
        deployment = self._deployment_for_pipeline(is_async=True)
        if deployment:
            return await deployment.async_infer(
                async_client=async_client,
                tensor=tensor,
                timeout=timeout,
                retries=retries,
                dataset=dataset,
                dataset_exclude=dataset_exclude,
                dataset_separator=dataset_separator,
            )
        else:
            raise RuntimeError(f"Pipeline {self.name} is not deployed")

    @staticmethod
    def _init_semaphore(
        deployment, num_parallel: Optional[int] = None
    ) -> asyncio.Semaphore:
        semaphore = num_parallel or 1
        if num_parallel is None:
            if not isinstance(deployment.engine_config(), DehydratedValue):
                eng_config = deployment.engine_config()
                if "engine" in eng_config and "replicas" in eng_config["engine"]:
                    # semaphore should be 2 to 4 times the number of replicas, to se performance boost
                    semaphore = eng_config["engine"]["replicas"] * 2
        return asyncio.Semaphore(semaphore)

    @staticmethod
    async def _bound_async_infer(
        deployment: Deployment,
        async_client: AsyncClient,
        semaphore: asyncio.Semaphore,
        tensor: Union[Dict[str, Any], pd.DataFrame, pa.Table],
        timeout: Optional[Union[int, float]] = None,
        retries: Optional[int] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
    ):
        async with semaphore:
            results = await deployment.async_infer(
                async_client=async_client,
                tensor=tensor,
                timeout=timeout,
                retries=retries,
                dataset=dataset,
                dataset_exclude=dataset_exclude,
                dataset_separator=dataset_separator,
            )
            return results

    async def _split_result_and_error(
        self,
        results_list: List[Union[pd.DataFrame, pa.Table, Exception]],
        batch_size_mapping: List[int],
        arrow: Optional[bool] = False,
    ):
        """
        Split the results into two lists, one containing the results and one containing the errors.
        :param: results: List[Union[pd.DataFrame, pa.Table, Exception]] The results from the async inference.
        :param: batch_size_mapping: List[int] A mapping that maintains the batch size for each item in the list.
        :param: arrow: Optional[bool] If set to True, return logs as an Arrow Table. Else, returns Pandas DataFrame.
        """
        data_list = []
        error_list = []
        error_count = 0
        sample_data = None
        for result in results_list:
            if isinstance(result, (pd.DataFrame, pa.Table)):
                sample_data = result
                break
        # If there is no sample data, return the error list
        if not isinstance(sample_data, (pa.Table, pd.DataFrame)):
            error_df = pd.DataFrame({"error": results_list})
            return pa.Table.from_pandas(error_df) if arrow else error_df

        for idx, result in enumerate(results_list):
            batch_size = batch_size_mapping[idx]
            if isinstance(result, (pd.DataFrame, pa.Table)):
                data_list.append(result)
                error_list += [""] * batch_size
            elif isinstance(result, Exception):
                data_list += [self._create_empty_row(sample_data, batch_size)]
                error_list += [str(result)] * batch_size
                error_count += 1

        if error_count == 0:
            return self._concat_data(data_list, arrow)
        else:
            final_data = self._concat_data(data_list, arrow)
            final_data = self._append_error_column(final_data, error_list, arrow)

            return final_data

    @staticmethod
    def _create_empty_row(
        sample_data: Union[pa.Table, pd.DataFrame],
        batch_size: int,
    ) -> Union[pa.Table, pd.DataFrame]:
        """
        Create an empty table with the same schema as the sample_table.
        :param: sample_table: pa.Table The table to use as a template.
        :return: pa.Table The empty table.
        """
        if isinstance(sample_data, pa.Table):
            return pa.table(
                {
                    field.name: pa.array([None] * batch_size, type=field.type)
                    for field in sample_data.schema
                }
            )
        else:
            return pd.DataFrame(
                "", index=np.arange(batch_size), columns=sample_data.columns
            )

    @staticmethod
    def _concat_data(data_list, arrow):
        if arrow:
            return pa.concat_tables(data_list, promote=True)
        else:
            return pd.concat(data_list, ignore_index=True)

    @staticmethod
    def _append_error_column(final_data, error_list, arrow):
        if arrow:
            final_data = final_data.append_column(
                "error", pa.array(error_list, pa.string())
            )
        else:
            final_data["error"] = error_list
        return final_data

    @staticmethod
    def _split_dataframe(df, batch_size):
        batches = list()
        no_of_batches = math.ceil(len(df) / batch_size)
        for i in range(no_of_batches):
            batches.append(df[i * batch_size : (i + 1) * batch_size])
        return batches

    async def _run_parallel_inferences_with_pandas_dataframe(
        self,
        deployment: Deployment,
        async_client: AsyncClient,
        semaphore: asyncio.Semaphore,
        tensor: pd.DataFrame,
        batch_size: int,
        timeout: Optional[Union[int, float]] = None,
        retries: Optional[int] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Run parallel inferences using pandas DataFrame. Splits the dataframe into chunks of size 1
        and runs the inferences in parallel.
        :param deployment: Deployment The deployment object.
        :param async_client: AsyncClient The asynchronous client.
        :param semaphore: asyncio.Semaphore The semaphore to limit the number of concurrent requests.
        :param tensor: pd.DataFrame The input data as a pandas DataFrame.
        :param batch_size: int The number of examples in a batch.
        :param timeout: Optional[Union[int, float]] The timeout for the request. Defaults to None.
        :param retries: Optional[int] The number of retries for the request. Defaults to None.
        :param dataset: Optional[List[str]] The list of dataset names to include. Defaults to None.
        :param dataset_exclude: Optional[List[str]] The list of dataset names to exclude. Defaults to None.
        :param dataset_separator: Optional[str] The separator for dataset names. Defaults to None.
        :return: pd.DataFrame The results of the async inference as a pandas DataFrame.
        """
        tensor_list = self._split_dataframe(tensor, batch_size)
        tasks = [
            self._bound_async_infer(
                deployment=deployment,
                async_client=async_client,
                semaphore=semaphore,
                tensor=df.reset_index(drop=True),  # type: ignore[attr-defined]
                timeout=timeout,
                retries=retries,
                dataset=dataset,
                dataset_exclude=dataset_exclude,
                dataset_separator=dataset_separator,
            )
            for df in tensor_list
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Create a mapping that maintains the batch size for each item in the list
        batch_size_mapping = [len(batch) for batch in tensor_list]
        results_df = await self._split_result_and_error(results, batch_size_mapping)
        return results_df

    async def _run_parallel_inferences_with_pyarrow_table(
        self,
        deployment: Deployment,
        async_client: AsyncClient,
        semaphore: asyncio.Semaphore,
        tensor: pa.Table,
        batch_size: int,
        timeout: Optional[Union[int, float]] = None,
        retries: Optional[int] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
    ) -> pa.Table:
        """
        Run parallel inferences using pyarrow Table. Splits the table into chunks of size 1 and runs the inference
        on each chunk.
        :param: deployment: Deployment The deployment object.
        :param: async_client: AsyncClient The asynchronous client.
        :param: semaphore: asyncio.Semaphore The semaphore to limit the number of concurrent requests.
        :param: tensor: pa.Table The input data as a pyarrow Table.
        :param: batch_size: int The number of examples in a batch.
        :param: timeout: Optional[Union[int, float]] The timeout for the request. Defaults to None.
        :param: retries: Optional[int] The number of retries for the request. Defaults to None.
        :param: dataset: Optional[List[str]] The list of dataset names to include. Defaults to None.
        :param: dataset_exclude: Optional[List[str]] The list of dataset names to exclude. Defaults to None.
        :param: dataset_separator: Optional[str] The separator for dataset names. Defaults to None.
        :return: pa.Table The results of the async inference as a pyarrow Table.
        """
        batches = tensor.to_batches(max_chunksize=batch_size)
        tasks = [
            self._bound_async_infer(
                deployment=deployment,
                async_client=async_client,
                semaphore=semaphore,
                tensor=pa.Table.from_batches([batch]),
                timeout=timeout,
                retries=retries,
                dataset=dataset,
                dataset_exclude=dataset_exclude,
                dataset_separator=dataset_separator,
            )
            for batch in batches
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Create a mapping that maintains the batch size (num rows) for each item in the RecordBatch
        batch_size_mapping = [batch.num_rows for batch in batches]
        result_table = await self._split_result_and_error(
            results, batch_size_mapping, arrow=True
        )
        return result_table

    async def parallel_infer(
        self,
        tensor: Union[pd.DataFrame, pa.Table],
        batch_size: Optional[int] = 1,
        timeout: Optional[Union[int, float]] = None,
        num_parallel: Optional[int] = None,
        retries: Optional[int] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
    ):
        """
        Runs parallel inferences and returns a list of inference results on latest deployment.
        :param: tensor: Union[pd.DataFrame, pa.Table] Inference data.
        :param: batch_size: Optional[int] Number of examples per batch.
        :param: timeout: Optional[Union[int, float]] infer requests will time out after the amount of
            seconds provided are exceeded. timeout defaults to 15 secs.
        :param: num_parallel: Optional[int] Semaphore to use for async inference.
        :param: retries: Optional[int] Number of retries to use in case of Connection errors.
        :param: dataset: Optional[List[str]] By default this is set to ["*"] which returns,
            ["time", "in", "out", "anomaly"]. Other available options - ["metadata"]
        :param: dataset_exclude: Optional[List[str]] If set, allows user to exclude parts of dataset.
        :param: dataset_separator: Optional[Union[Sequence[str], str]] If set to ".", return dataset will be flattened.
        :return: Union[pd.DataFrame, pa.Table] Inference results
        """
        deployment = self._deployment_for_pipeline()
        semaphore = self._init_semaphore(deployment, num_parallel)

        if tensor is None or not isinstance(tensor, (pd.DataFrame, pa.Table)):
            raise ValueError("tensor must be a pandas DataFrame or a pyarrow Table")

        if batch_size is None or batch_size == 0:
            raise ValueError(
                "batch_size must be a positive integer and cannot be None or 0"
            )

        if deployment:
            async with httpx.AsyncClient() as async_client:
                if isinstance(tensor, pd.DataFrame):
                    return await self._run_parallel_inferences_with_pandas_dataframe(
                        deployment=deployment,
                        async_client=async_client,
                        semaphore=semaphore,
                        tensor=tensor,
                        batch_size=batch_size,
                        timeout=timeout,
                        retries=retries,
                        dataset=dataset,
                        dataset_exclude=dataset_exclude,
                        dataset_separator=dataset_separator,
                    )
                elif isinstance(tensor, pa.Table):
                    return await self._run_parallel_inferences_with_pyarrow_table(
                        deployment=deployment,
                        async_client=async_client,
                        semaphore=semaphore,
                        tensor=tensor,
                        batch_size=batch_size,
                        timeout=timeout,
                        retries=retries,
                        dataset=dataset,
                        dataset_exclude=dataset_exclude,
                        dataset_separator=dataset_separator,
                    )
        else:
            raise RuntimeError(f"Pipeline {self.name} is not deployed")

    def status(self) -> Dict[str, Any]:
        """Status of pipeline"""
        deployment = self._deployment_for_pipeline()
        if deployment:
            return deployment.status()
        else:
            return {"status": f"Pipeline {self.name()} is not deployed"}

    # -----------------------------------------------------------------------------
    # Accessors for PipelineConfigBuilder attributes. Not exactly shims and they may be changing a
    # contract elsewhere.
    # -----------------------------------------------------------------------------

    def steps(self) -> List[Step]:
        """Returns a list of the steps of a pipeline. Not exactly a shim"""
        return self.builder().steps

    def model_configs(self) -> List[ModelConfig]:
        """Returns a list of the model configs of a pipeline. Not exactly a shim"""
        return self.builder()._model_configs()

    # -----------------------------------------------------------------------------
    # Shims for PipelineConfigBuilder methods
    # -----------------------------------------------------------------------------

    def _upload(self) -> "Pipeline":
        assert self.client is not None

        # Special case: deploying an existing pipeline where pipeline steps are of type ModelInference
        # The builder doesn't get repopulated so we do that here.

        if self.builder().steps == []:
            use_this_pipeline_version = (
                self._pipeline_version_to_deploy or self.versions()[0]
            )
            for step in use_this_pipeline_version.definition()["steps"]:
                if "ModelInference" in step:
                    name = step["ModelInference"]["models"][0]["name"]
                    version = step["ModelInference"]["models"][0]["version"]
                    model = self.client.model_version_by_name(
                        model_class=name, model_name=version
                    )
                    self.add_model_step(model)

        new_pipeline = self.builder().upload()
        self._fill({"id": new_pipeline.id()})
        return self

    def remove_step(self, index: int) -> "Pipeline":
        """Remove a step at a given index"""
        self.builder().remove_step(index)
        return self

    def add_model_step(self, model_version: ModelVersion) -> "Pipeline":
        """Perform inference with a single model."""
        self.builder().add_model_step(model_version)
        return self

    def replace_with_model_step(
        self, index: int, model_version: ModelVersion
    ) -> "Pipeline":
        """Replaces the step at the given index with a model step"""
        self.builder().replace_with_model_step(index, model_version)
        return self

    def add_multi_model_step(
        self, model_version_list: Iterable[ModelVersion]
    ) -> "Pipeline":
        """Perform inference on the same input data for any number of models."""
        self.builder().add_multi_model_step(model_version_list)
        return self

    def replace_with_multi_model_step(
        self, index: int, model_version_list: Iterable[ModelVersion]
    ) -> "Pipeline":
        """Replaces the step at the index with a multi model step"""
        self.builder().replace_with_multi_model_step(index, model_version_list)
        return self

    def add_audit(self, slice) -> "Pipeline":
        """Run audit logging on a specified `slice` of model outputs.

        The slice must be in python-like format. `start:`, `start:end`, and
        `:end` are supported.
        """
        self.builder().add_audit(slice)
        return self

    def replace_with_audit(self, index: int, audit_slice: str) -> "Pipeline":
        """Replaces the step at the index with an audit step"""
        self.builder().replace_with_audit(index, audit_slice)
        return self

    def add_select(self, index: int) -> "Pipeline":
        """Select only the model output with the given `index` from an array of
        outputs.
        """
        self.builder().add_select(index)
        return self

    def replace_with_select(self, step_index: int, select_index: int) -> "Pipeline":
        """Replaces the step at the index with a select step"""
        self.builder().replace_with_select(step_index, select_index)
        return self

    def add_key_split(
        self, default: ModelVersion, meta_key: str, options: Dict[str, ModelVersion]
    ) -> "Pipeline":
        """Split traffic based on the value at a given `meta_key` in the input data,
        routing to the appropriate model.

        If the resulting value is a key in `options`, the corresponding model is used.
        Otherwise, the `default` model is used for inference.
        """
        self.builder().add_key_split(default, meta_key, options)
        return self

    def replace_with_key_split(
        self,
        index: int,
        default: ModelVersion,
        meta_key: str,
        options: Dict[str, ModelVersion],
    ) -> "Pipeline":
        """Replace the step at the index with a key split step"""
        self.builder().replace_with_key_split(index, default, meta_key, options)
        return self

    def add_random_split(
        self,
        weighted: Iterable[Tuple[float, ModelVersion]],
        hash_key: Optional[str] = None,
    ) -> "Pipeline":
        """Routes inputs to a single model, randomly chosen from the list of
        `weighted` options.

        Each model receives inputs that are approximately proportional to the
        weight it is assigned.  For example, with two models having weights 1
        and 1, each will receive roughly equal amounts of inference inputs. If
        the weights were changed to 1 and 2, the models would receive roughly
        33% and 66% respectively instead.

        When choosing the model to use, a random number between 0.0 and 1.0 is
        generated. The weighted inputs are mapped to that range, and the random
        input is then used to select the model to use. For example, for the
        two-models equal-weight case, a random key of 0.4 would route to the
        first model. 0.6 would route to the second.

        To support consistent assignment to a model, a `hash_key` can be
        specified. This must be between 0.0 and 1.0. The value at this key, when
        present in the input data, will be used instead of a random number for
        model selection.
        """
        self.builder().add_random_split(weighted, hash_key)
        return self

    def replace_with_random_split(
        self,
        index: int,
        weighted: Iterable[Tuple[float, ModelVersion]],
        hash_key: Optional[str] = None,
    ) -> "Pipeline":
        """Replace the step at the index with a random split step"""
        self.builder().replace_with_random_split(index, weighted, hash_key)
        return self

    def add_shadow_deploy(
        self, champion: ModelVersion, challengers: Iterable[ModelVersion]
    ) -> "Pipeline":
        """Create a "shadow deployment" experiment pipeline. The `champion`
        model and all `challengers` are run for each input. The result data for
        all models is logged, but the output of the `champion` is the only
        result returned.

        This is particularly useful for "burn-in" testing a new model with real
        world data without displacing the currently proven model.

        This is currently implemented as three steps: A multi model step, an audit step, and
        a select step. To remove or replace this step, you need to remove or replace
        all three. You can remove steps using pipeline.remove_step
        """
        self.builder().add_shadow_deploy(champion, challengers)
        return self

    def replace_with_shadow_deploy(
        self, index: int, champion: ModelVersion, challengers: Iterable[ModelVersion]
    ) -> "Pipeline":
        """Replace a given step with a shadow deployment"""
        self.builder().replace_with_shadow_deploy(index, champion, challengers)
        return self

    def add_validations(self, **validations: polars.Expr) -> "Pipeline":
        """Add a dict of `validations` to run on every row."""
        self.builder().add_validations(**validations)
        return self

    def clear(self) -> "Pipeline":
        """
        Remove all steps from the pipeline. This might be desireable if replacing models, for example.
        """
        self.builder().clear()
        return self

    def publish(
        self,
        deployment_config: Optional[DeploymentConfig] = None,
        replaces: Optional[List[int]] = None,
    ):
        """Create a new version of a pipeline and publish it."""

        # upload the pipeline version to save the step information (usually only saved on deploy)
        self._upload()

        return self.versions()[0].publish(deployment_config, replaces)

    def publishes(self):
        from http import HTTPStatus

        from .wallaroo_ml_ops_api_client.api.pipelines.list_publishes_for_pipeline import (
            ListPublishesForPipelineBody,
            sync_detailed,
        )

        ret = sync_detailed(
            client=self.client.mlops(),
            body=ListPublishesForPipelineBody(self.id()),
        )

        if ret.status_code != HTTPStatus.OK:
            raise Exception("Failed to list publishes for pipeline")

        # FIXME: The MLOps client library should automatically parse this in ret.parsed.
        # The fact that it fails to do so may be indicative of a bug in the OpenAPI schema.
        import json

        json_ret = json.loads(ret.content)

        return PipelinePublishList(
            [
                PipelinePublish(client=self.client, **pub)
                for pub in json_ret["publishes"]
            ]
        )

    def list_edges(self):
        from http import HTTPStatus

        from .wallaroo_ml_ops_api_client.api.pipelines.list_publishes_for_pipeline import (
            ListPublishesForPipelineBody,
            sync_detailed,
        )

        ret = sync_detailed(
            client=self.client.mlops(),
            body=ListPublishesForPipelineBody(self.id()),
        )

        if ret.status_code != HTTPStatus.OK:
            raise Exception("Failed to list publishes for pipeline")

        # FIXME: The MLOps client library should automatically parse this in ret.parsed.
        # The fact that it fails to do so may be indicative of a bug in the OpenAPI schema.
        import json

        json_ret = json.loads(ret.content)
        return EdgeList([Edge(**pub) for pub in json_ret["edges"]])

    def create_version(self) -> "PipelineVersion":
        """Creates a new PipelineVersion and stores it in the database."""
        return self.builder().upload().versions()[0]

    def openai_completion(self, **kwargs):
        openai_completions_url = self.url() + "/openai/v1"
        openai_client = OpenAI(
            base_url=openai_completions_url,
            api_key=self.client.auth._access_token().token,
        )
        response = openai_client.completions.create(
            model="",
            **kwargs,
        )
        return response

    def openai_chat_completion(self, **kwargs):
        openai_completions_url = self.url() + "/openai/v1"
        openai_client = OpenAI(
            base_url=openai_completions_url,
            api_key=self.client.auth._access_token().token,
        )
        response = openai_client.chat.completions.create(
            model="",
            **kwargs,
        )
        return response

    def get_external_url(self):
        from http import HTTPStatus

        from .wallaroo_ml_ops_api_client.api.admin.admin_get_pipeline_external_url import (
            AdminGetPipelineExternalUrlBody,
            sync_detailed,
        )

        url = sync_detailed(
            client=self.client.mlops(),
            body=AdminGetPipelineExternalUrlBody(
                workspace_id=self.workspace().id(), pipeline_name=self.name()
            ),
        )
        if url.status_code != HTTPStatus.OK:
            raise Exception("Failed to get pipeline external url")
        return url.parsed.url

    def generate_api_spec(self, path: str | None = None):
        deployment = self._deployment_for_pipeline()
        if deployment is None:
            raise Exception("Pipeline is not deployed")
        model_configs = deployment.model_configs()
        [mc._rehydrate() for mc in model_configs]

        if model_configs is None or len(model_configs) == 0:
            raise Exception("Pipeline has no model configs")

        try:
            pipeline_version = deployment.pipeline_versions()[0]
            version = pipeline_version.name()
            definition = pipeline_version.definition()
            pipeline_name = definition["id"]
            steps = definition.get("steps", [])
            first_step_model_version = steps[0]["ModelInference"]["models"][0][
                "version"
            ]
            last_step_model_version = steps[-1]["ModelInference"]["models"][0][
                "version"
            ]
            first_model_config = next(
                mc
                for mc in model_configs
                if mc.model_version().version() == first_step_model_version
            )
            last_model_config = next(
                mc
                for mc in model_configs
                if mc.model_version().version() == last_step_model_version
            )
        except Exception as e:
            raise Exception(f"Couldn't determine first/last step's model config: {e}")

        url = self.get_external_url()

        with open(path or f"{pipeline_name}.yaml", "w") as f:
            if last_model_config.openai_config() is not None:
                f.write(
                    WITH_OPENAI.format(
                        pipeline_name=pipeline_name, version=version, url=url
                    )
                )
            else:
                input_schema = output_schema = DEFAULT_SCHEMA
                flattened_input_schema = flattened_output_schema = ""
                if first_model_config.input_schema() is not None:
                    schema = decode_arrow_schema_from_base64(
                        first_model_config.input_schema()
                    )
                    input_schema = arrow_schema_to_openapi_yaml(schema, indent=8)
                    flattened_input_schema = arrow_schema_to_openapi_yaml(
                        schema, indent=12, prepend_props="in."
                    )
                if last_model_config.output_schema() is not None:
                    schema = decode_arrow_schema_from_base64(
                        last_model_config.output_schema()
                    )
                    output_schema = arrow_schema_to_openapi_yaml(schema, indent=14)
                    flattened_output_schema = arrow_schema_to_openapi_yaml(
                        schema, indent=12, prepend_props="out."
                    )
                f.write(
                    WITHOUT_OPENAI.format(
                        pipeline_name=pipeline_name,
                        version=version,
                        url=url,
                        input_schema=input_schema,
                        output_schema=output_schema,
                        flattened_input_schema=flattened_input_schema,
                        flattened_output_schema=flattened_output_schema,
                    )
                )


class Pipelines(List[Pipeline]):
    """Wraps a list of pipelines for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(pipeline):
            steptable = pipeline._html_steptable()
            fmt = pipeline.client._time_format
            tags = ", ".join([tag.tag() for tag in pipeline.tags()])
            deployment = pipeline._deployment_for_pipeline()
            depstr = "(unknown)" if deployment is None else deployment.deployed()
            arch = (
                None
                if deployment is None
                else deployment.engine_config()
                .get("engine", dict())
                .get("arch", str(Architecture.default()))
            )
            accel = _accel_from_deployment_or_model_configs(
                deployment, pipeline.model_configs()
            )
            versions = ", ".join([version.name() for version in pipeline.versions()])

            return (
                "<tr>"
                + f"<td>{pipeline.name()}</td>"
                + f"<td>{pipeline.create_time().strftime(fmt)}</td>"
                + f"<td>{pipeline.last_update_time().strftime(fmt)}</td>"
                + f"<td>{depstr}</td>"
                + f"<td>{pipeline.workspace().id()}</td>"
                + f"<td>{pipeline.workspace().name()}</td>"
                + f"<td>{arch}</td>"
                + f"<td>{accel}</td>"
                + f"<td>{tags}</td>"
                + f"<td>{versions}</td>"
                + f"<td>{steptable}</td>"
                + f"<td>{True if any([len(version._publishes) > 0 for version in pipeline.versions()]) > 0 else False}</td>"
                + "</tr>"
            )

        fields = [
            "name",
            "created",
            "last_updated",
            "deployed",
            "workspace_id",
            "workspace_name",
            "arch",
            "accel",
            "tags",
            "versions",
            "steps",
            "published",
        ]

        if self == []:
            return "(no pipelines)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )
