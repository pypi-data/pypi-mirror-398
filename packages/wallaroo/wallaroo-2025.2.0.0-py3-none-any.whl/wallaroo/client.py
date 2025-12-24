import base64
import json
import os
import pathlib
import posixpath
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from itertools import chain, repeat
from typing import Any, Dict, List, NewType, Optional, Tuple, Union, cast
from urllib.parse import quote_plus

import dateutil
import gql
import httpx  # type: ignore
import numpy as np
import pandas as pd
import pyarrow as pa  # type: ignore
from gql.transport.httpx import HTTPXTransport

import wallaroo.config as global_config
from wallaroo.assays_v2 import (
    AssayV2,
    AssayV2List,
    Summarizer,
    SummaryBaseline,
    Targeting,
)
from wallaroo.custom_types import IAssayAnalysisList
from wallaroo.exceptions import ModelUploadError, handle_errors
from wallaroo.http_utils import _setup_http_client
from wallaroo.model import Model, ModelList
from wallaroo.model_registry import ModelRegistriesList, ModelRegistry
from wallaroo.utils import _unwrap
from wallaroo.wallaroo_ml_ops_api_client.models.interval_unit import IntervalUnit
from wallaroo.wallaroo_ml_ops_api_client.models.run_frequency_type_1 import (
    RunFrequencyType1,
)

from . import auth
from ._datasizeunit import DataSizeUnit
from ._inference_decode import inference_logs_to_dataframe, nested_df_to_flattened_df
from .assay import Assay, AssayAnalysis, AssayAnalysisList, Assays
from .assay_config import (
    AssayBuilder,
    AssayConfig,
    CalculatedBaseline as V1CalculatedBaseline,
    FixedBaseline as V1FixedBaseline,
    StaticBaseline as V1StaticBaseline,
    UnivariateContinousSummarizerConfig,
)
from .connection import Connection, ConnectionList
from .deployment import Deployment
from .engine_config import (
    Acceleration,
    AccelerationWithConfig,
    Architecture,
    InvalidAccelerationError,
)
from .framework import Framework, FrameworkConfig
from .model_config import ModelConfig
from .model_version import ModelVersion, ModelVersionList
from .object import (
    EntityNotFoundError,
    ModelConversionError,
    ModelConversionTimeoutError,
)
from .orchestration import Orchestration
from .pipeline import Pipeline, Pipelines
from .pipeline_config import PipelineConfig
from .pipeline_publish import PipelinePublish, PipelinePublishList
from .pipeline_version import PipelineVersion, PipelineVersionList
from .tag import Tag, Tags
from .task import Task
from .user import User
from .utils import (
    _ensure_tz,
    create_new_file,
    is_assays_v2_enabled,
    require_dns_compliance,
    write_to_file,
)
from .version import _user_agent
from .visibility import _Visibility
from .wallaroo_ml_ops_api_client.api.assay import (
    assays_create,
    assays_get_assay_results,
    assays_list,
    assays_set_active,
)
from .wallaroo_ml_ops_api_client.api.assays.schedule import (
    ScheduleBody,
    sync_detailed as sync,
)
from .wallaroo_ml_ops_api_client.api.pipelines import pipelines_create
from .wallaroo_ml_ops_api_client.api.pipelines.list_publishes_for_pipeline import (
    ListPublishesForPipelineBody,
    sync_detailed as sync_list_publishes_for_pipeline,
)
from .wallaroo_ml_ops_api_client.api.pipelines.remove_edge import (
    RemoveEdgeBody,
    sync_detailed as removeEdgeSync,
)
from .wallaroo_ml_ops_api_client.client import AuthenticatedClient as MLOpsClient
from .wallaroo_ml_ops_api_client.models import (
    AssaysSetActiveBody,
    AssaysSetActiveResponse200,
    assays_get_assay_results_body,
    pipelines_create_body,
    pipelines_create_body_definition_type_0,
)
from .wallaroo_ml_ops_api_client.models.assays_create_body import AssaysCreateBody
from .wallaroo_ml_ops_api_client.models.assays_create_response_200 import (
    AssaysCreateResponse200,
)
from .wallaroo_ml_ops_api_client.models.assays_get_assay_results_response_200_item import (
    AssaysGetAssayResultsResponse200Item,
)
from .wallaroo_ml_ops_api_client.models.assays_list_body import AssaysListBody
from .wallaroo_ml_ops_api_client.models.baseline_type_1 import (
    BaselineType1 as V2StaticBaseline,
)
from .wallaroo_ml_ops_api_client.models.pg_interval import PGInterval
from .wallaroo_ml_ops_api_client.models.pipelines_create_response_200 import (
    PipelinesCreateResponse200,
)
from .wallaroo_ml_ops_api_client.models.rolling_window import RollingWindow
from .wallaroo_ml_ops_api_client.models.scheduling import Scheduling
from .wallaroo_ml_ops_api_client.models.window_width_duration import WindowWidthDuration
from .wallaroo_ml_ops_api_client.types import UNSET
from .workspace import Workspace

Datetime = NewType("Datetime", datetime)

WALLAROO_SDK_AUTH_TYPE = "WALLAROO_SDK_AUTH_TYPE"
WALLAROO_URL = "WALLAROO_URL"

ARROW_CONTENT_TYPE = "application/vnd.apache.arrow.file"
JSON_CONTENT_TYPE = "application/json"
OCTET_STREAM_CONTENT_TYPE = "application/octet-stream"

UPLOAD_MODEL_STREAM_SUPPORTED_FLAVORS = [
    Framework.ONNX,
    Framework.TENSORFLOW,
]
DEFAULT_MODEL_CONVERSION_TIMEOUT = 60 * 30  # 30 minutes
DEFAULT_MODEL_CONVERSION_PYTHON_VERSION = "3.8"

DEFAULT_RECORDS_LIMIT = 100
DEFAULT_RECORDS_BY_TIME_LIMIT = 1_000_000
DEFAULT_MAX_DATA_SIZE = 100  # type: float
DEFAULT_MAX_DATA_UNIT = DataSizeUnit.MiB


class Client(object):
    """Client handle to a Wallaroo platform instance.

    Objects of this class serve as the entrypoint to Wallaroo platform
    functionality.
    """

    @staticmethod
    def get_urls(
        auth_type: Optional[str] = None,
        api_endpoint: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Method to calculate the auth values specified as defaults,
        as params or in ENV vars.
        Made static to be testable without reaching out to SSO, etc."""

        # If this is set, we are running in a pipeline orchestration deployment, meaning: we
        # override auth type because no other auth type provided in user code will work. Also, this
        # lets the user write a plain notebook and that does wallaroo.Client(auth_type=WHATEVER)
        # and upload it as an orchestration, and we will handle it silently.

        if os.getenv("WALLAROO_TASK_ID"):
            auth_type = "orch"

        elif auth_type is None:
            auth_type = os.environ.get(WALLAROO_SDK_AUTH_TYPE, None)

        if api_endpoint is None or len(api_endpoint.strip()) == 0:
            api_endpoint = os.environ.get(WALLAROO_URL, None)

        if any(x is None for x in [auth_type, api_endpoint]):
            raise ValueError(
                "auth_type, and api_endpoint must be provided or set in environment as \n"
                "`WALLAROO_SDK_AUTH_TYPE`, and `WALLAROO_URL` respectively.\n"
            )
        return auth_type, api_endpoint

    def __init__(
        self,
        api_endpoint: Optional[str] = None,
        request_timeout: Optional[int] = None,
        auth_type: Optional[str] = None,
        gql_client: Optional[gql.Client] = None,
        interactive: Optional[bool] = None,
        time_format: str = "%Y-%d-%b %H:%M:%S",
        config: Optional[dict] = None,
    ):
        """Create a Client handle.

        :param Optional[str] api_endpoint: Host/port of the platform API endpoint. If not provided, the value of the `WALLAROO_URL` environment variable will be used.
        :param Optional[int] request_timeout: Max timeout of web requests, in seconds
        :param Optional[str] auth_type: Authentication type to use. Can be one of: "none",
            "sso", "user_password".
        :param Optional[bool] interactive: If provided and True, some calls will print additional human information, or won't when False. If not provided, interactive defaults to True if running inside Jupyter and False otherwise.
        :param str time_format: Preferred `strftime` format string for displaying timestamps in a human context.
        """

        auth_type, api_endpoint = Client.get_urls(auth_type, api_endpoint)
        # no way these are none at this point, just making mypy happy
        assert auth_type is not None
        assert api_endpoint is not None

        self.auth = auth.create(api_endpoint, auth_type)

        if request_timeout is None:
            request_timeout = int(os.getenv("WALLAROO_REQUEST_TIMEOUT", 45))

        if gql_client:
            self._gql_client = gql_client
        else:
            gql_transport = HTTPXTransport(
                url=posixpath.join(api_endpoint, "v1/graphql"),
                auth=self.auth,
                timeout=request_timeout,
            )
            self._gql_client = gql.Client(
                transport=gql_transport, fetch_schema_from_transport=True
            )

        self.api_endpoint = api_endpoint.rstrip("/")

        self.timeout = request_timeout

        self._http_client: Optional[httpx.Client] = None
        self._http_client_initialized = False

        self._setup_mlops_client()

        self._current_workspace: Optional[Workspace] = None

        # TODO: debate the names of these things
        self._default_ws_name: Optional[str] = None

        user_email = self.auth.user_email()
        if user_email is not None:
            self._default_ws_name = user_email + "_ws"

        if interactive is not None:
            self._interactive = interactive
        elif (
            "JUPYTER_SVC_SERVICE_HOST" in os.environ or "JUPYTERHUB_HOST" in os.environ
        ):
            self._interactive = True
        else:
            self._interactive = False

        self._time_format = time_format

        self._in_task = "WALLAROO_TASK_ID" in os.environ
        self._task_args_filename = "/home/jovyan/arguments.json"

        if config is None:
            headers = {
                "user-agent": _user_agent,
            }
            url = f"{self.api_endpoint}/v1/api/config"
            resp = httpx.get(url, headers=headers)
            resp.raise_for_status()
            global_config._config = resp.json()
        else:
            global_config._config = config

    @property
    def httpx_client(self) -> httpx.Client:
        """Lazy HTTP client property that creates the client on first use."""
        if self._http_client is None:
            self._http_client = _setup_http_client(self)
            self._http_client_initialized = True
        return self._http_client

    def list_tags(self) -> Tags:
        """List all tags on the platform.

        :return: A list of all tags on the platform.
        :rtype: List[Tag]
        """
        res = self._gql_client.execute(
            gql.gql(
                """
            query ListTags {
              tag(order_by: {id: desc}) {
                id
                tag
                model_tags {
                  model {
                    id
                    model_id
                    models_pk_id
                    model_version

                  }
                }
                pipeline_tags {
                  pipeline {
                    id
                    pipeline_id
                    pipeline_versions {
                        id
                        version
                    }
                  }
                }
              }
            }


            """
            )
        )
        return Tags([Tag(client=self, data={"id": p["id"]}) for p in res["tag"]])

    def _build_list_models_request(self, workspace_id, workspace_name):
        if workspace_name is not None:
            request_dict = {
                "workspace_id": workspace_id,
                "workspace_name": workspace_name,
            }
        else:
            request_dict = {
                "workspace_id": (workspace_id or self.get_current_workspace().id()),
                "workspace_name": workspace_name,
            }
        return request_dict

    def list_models(
        self, workspace_id: Optional[int] = None, workspace_name: Optional[str] = None
    ) -> ModelList:
        """List all models in the current or a specified workspace.
        :param workspace_id: Optional[int]: The workspace id to search in. If not provided, the current workspace id is used.
        :param workspace_name: Optional[str]: The workspace name to search in. If not provided, the current workspace name is used.
        :return: A list of all models in the workspace.
        :rtype: List[ModelVersion]
        """
        from wallaroo.wallaroo_ml_ops_api_client.api.model.list_models import sync
        from wallaroo.wallaroo_ml_ops_api_client.models.list_models_request import (
            ListModelsRequest,
        )

        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        request_dict = self._build_list_models_request(workspace_id, workspace_name)
        res = sync(
            client=self.mlops(),
            body=ListModelsRequest.from_dict(request_dict),
        )

        if res is None:
            raise Exception("Failed to list models")

        return ModelList(
            [Model(client=self, data=v.model.to_dict()) for v in res.models]
        )

    def list_deployments(self) -> List[Deployment]:
        """List all deployments (active or not) on the platform.

        :return: A list of all deployments on the platform.
        :rtype: List[Deployment]
        """
        res = self._gql_client.execute(
            gql.gql(
                """
            query ListDeployments {
              deployment {
                id
                deploy_id
                deployed
                deployment_model_configs {
                  model_config {
                    id
                  }
                }
              }
            }
            """
            )
        )
        return [Deployment(client=self, data=d) for d in res["deployment"]]

    """
        # Removed until we figure out what pipeline ownership means
        #
        # def search_my_pipelines(
        #     self,
        #     search_term: Optional[str] = None,
        #     deployed: Optional[bool] = None,
        #     created_start: Optional["Datetime"] = None,
        #     created_end: Optional["Datetime"] = None,
        #     updated_start: Optional["Datetime"] = None,
        #     updated_end: Optional["Datetime"] = None,
        # ) -> List[Pipeline]:
        #     user_id = self.auth.user_id()
        #     return Pipelines(
        #         self._search_pipelines(
        #             search_term,
        #             deployed,
        #             user_id,
        #             created_start,
        #             created_end,
        #             updated_start,
        #             updated_end,
        #         )
        #     )
    """

    def list_publishes(
        self, workspace_id: Optional[int] = None, workspace_name: Optional[str] = None
    ) -> List[PipelinePublish]:
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        workspace_id = self._get_id_for_workspace(workspace_id, workspace_name)
        ret = sync_list_publishes_for_pipeline(
            client=self.mlops(),
            body=ListPublishesForPipelineBody(
                pipeline_id=UNSET, workspace_id=workspace_id
            ),
        )
        if ret.status_code != HTTPStatus.OK:
            raise Exception("Failed to list publishes for pipeline")

        # FIXME: The MLOps client library should automatically parse this in ret.parsed.
        # The fact that it fails to do so may be indicative of a bug in the OpenAPI schema.
        # import json

        json_ret = json.loads(ret.content)

        return PipelinePublishList(
            [PipelinePublish(client=self, **pub) for pub in json_ret["publishes"]]
        )

    def search_pipelines(
        self,
        search_term: Optional[str] = None,
        deployed: Optional[bool] = None,
        created_start: Optional["Datetime"] = None,
        created_end: Optional["Datetime"] = None,
        updated_start: Optional["Datetime"] = None,
        updated_end: Optional["Datetime"] = None,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> PipelineVersionList:
        """Search for pipelines. All parameters are optional, in which case the result is the same as
        `list_pipelines()`. All times are strings to be parsed by `datetime.isoformat`. Example:

             myclient.search_pipelines(created_end='2022-04-19 13:17:59+00:00', search_term="foo")

        :param str search_term: Will be matched against tags and model names. Example: "footag123".
        :param bool deployed: Pipeline was deployed or not
        :param str created_start: Pipeline was created at or after this time
        :param str created_end: Pipeline was created at or before this time
        :param str updated_start: Pipeline was updated at or before this time
        :param str updated_end: Pipeline was updated at or before this time
        :param int workspace_id: The workspace id to search in
        :param str workspace_name: The workspace name to search in

        :return: A list of pipeline versions matching the search criteria.
        :rtype: List[PipelineVersion]
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        return PipelineVersionList(
            self._search_pipeline_versions(
                search_term,
                deployed,
                None,
                created_start,
                created_end,
                updated_start,
                updated_end,
                workspace_id,
                workspace_name,
            )
        )

    def search_pipeline_versions(
        self,
        search_term: Optional[str] = None,
        deployed: Optional[bool] = None,
        created_start: Optional["Datetime"] = None,
        created_end: Optional["Datetime"] = None,
        updated_start: Optional["Datetime"] = None,
        updated_end: Optional["Datetime"] = None,
    ) -> PipelineVersionList:
        """Search for pipeline versions. All parameters are optional. All times are strings to be parsed by
        `datetime.isoformat`.
        Example:
            >>> myclient.search_pipeline_versions(created_end='2022-04-19 13:17:59+00:00', search_term="foo")

        :param str search_term: Will be matched against tags and model names. Example: "footag123".
        :param bool deployed: Pipeline was deployed or not
        :param str created_start: Pipeline was created at or after this time
        :param str created_end: Pipeline was created at or before this time
        :param str updated_start: Pipeline was updated at or before this time
        :param str updated_end: Pipeline was updated at or before this time

        :return: A list of pipeline versions matching the search criteria.
        :rtype: List[PipelineVersion]
        """
        return PipelineVersionList(
            self._search_pipeline_versions(
                search_term,
                deployed,
                None,
                created_start,
                created_end,
                updated_start,
                updated_end,
            )
        )

    def _search_pipeline_versions(
        self,
        search_term: Optional[str] = None,
        deployed: Optional[bool] = None,
        user_id: Optional[str] = None,
        created_start: Optional["Datetime"] = None,
        created_end: Optional["Datetime"] = None,
        updated_start: Optional["Datetime"] = None,
        updated_end: Optional["Datetime"] = None,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> List[PipelineVersion]:
        (query, params) = self._generate_search_pipeline_query(
            search_term=search_term,
            deployed=deployed,
            user_id=user_id,
            created_start=created_start,
            created_end=created_end,
            updated_start=updated_start,
            updated_end=updated_end,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
        )
        q = gql.gql(query)
        data = self._gql_client.execute(q, variable_values=params)
        pipelines = []
        if data["search_pipelines"]:
            for p in data["search_pipelines"]:
                pipelines.append(PipelineVersion(self, p))
        return pipelines

    def _generate_search_pipeline_query(
        self,
        search_term: Optional[str] = None,
        deployed: Optional[bool] = None,
        user_id: Optional[str] = None,
        created_start: Optional["Datetime"] = None,
        created_end: Optional["Datetime"] = None,
        updated_start: Optional["Datetime"] = None,
        updated_end: Optional["Datetime"] = None,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ):
        filters: List[str] = []
        query_params: List[str] = []
        params: Dict[str, Any] = {}
        search = ""
        if search_term:
            search = search_term
        params["search_term"] = search
        query_params.append("$search_term: String!")

        self._add_filter_and_param_to_query(
            filters, params, query_params, "owner_id", "user_id", user_id, "String"
        )
        # build nested pipeline where clause
        pipeline_filters: List[str] = []
        self._add_workspace_filtering(
            pipeline_filters, params, query_params, workspace_id, workspace_name
        )
        if deployed is not None:
            deployment_filters: List[str] = []
            self._add_filter_and_param_to_query(
                deployment_filters,
                params,
                query_params,
                "deployed",
                "deployed",
                deployed,
                "Boolean",
            )
            self._build_nested_query(pipeline_filters, "deployment", deployment_filters)

        self._build_nested_query(filters, "pipeline", pipeline_filters)

        self._generate_time_range_graphql(
            "created_at",
            start=created_start,
            end=created_end,
            filters=filters,
            query_params=query_params,
            params=params,
        )
        self._generate_time_range_graphql(
            "updated_at",
            start=updated_start,
            end=updated_end,
            filters=filters,
            query_params=query_params,
            params=params,
        )

        where_clause_str = self._generate_where_clause_str(filters)
        query_param_str = self._generate_query_param_str(query_params)
        query = f"""
            query GetPipelines({query_param_str}) {{
                search_pipelines(args: {{search: $search_term}}, distinct_on: id{where_clause_str}, order_by: {{id: desc}}) {{
                    id
                    created_at
                    pipeline_pk_id
                    updated_at
                    version
                    pipeline {{
                        id
                        pipeline_id
                        pipeline_tags {{
                            id
                            tag {{
                                id
                                tag
                            }}
                        }}
                        workspace {{
                            id
                            name
                        }}
                    }}
                }}
            }}
        """
        return query, params

    def _generate_where_clause_str(self, filters: List[str]) -> str:
        where_clause_str = ""
        filters_len = len(filters)
        if filters_len > 0:
            if filters_len > 1:
                where_clause_str = f""", where: {{_and: [{", ".join(f"{{{fs}}}" for fs in filters)}] }}"""
            else:
                where_clause_str = f", where: {{{filters[0]}}}"
        return where_clause_str

    def _generate_query_param_str(self, query_params: List[str]):
        return ", ".join(query_params)

    def _generate_time_range_graphql(
        self,
        field: str,
        start: Optional["Datetime"],
        end: Optional["Datetime"],
        filters: List[str],
        query_params: List[str],
        params: Dict[str, Any],
    ):
        filter_condition = ""
        if start:
            iso_start = start.isoformat()
            params[f"start_{field}"] = iso_start
            query_params.append(f"$start_{field}: timestamptz!")
            filter_condition += f"_gte: $start_{field}"
        if end:
            iso_end = end.isoformat()
            params[f"end_{field}"] = iso_end
            query_params.append(f"$end_{field}: timestamptz!")
            if filter_condition:
                filter_condition += ", "
            filter_condition += f"_lte: $end_{field}"

        if filter_condition:
            filters.append(f"{field}: {{{filter_condition}}}")

    # TODO: Misleading name, this is actually searching for all model versions.
    # Future work will redo the query to give models instead of versions.
    def _search_my_models(
        self,
        search_term: Optional[str] = None,
        uploaded_time_start: Optional["Datetime"] = None,
        uploaded_time_end: Optional["Datetime"] = None,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> ModelVersionList:
        """Search models owned by you.
            Example:
                >>> client.search_my_models(search_term="my_model")
        :param search_term: Optional[str]: Searches the following metadata: names, shas, versions, file names, and tags
        :param uploaded_time_start: Optional[Datetime]: Inclusive time of upload
        :param uploaded_time_end: Optional[Datetime]:  Inclusive time of upload
        :param workspace_id: Optional[int]: The workspace id to search in
        :param workspace_name: Optional[str]: The workspace name to search in
        :param
        :return: ModelVersionList
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        user_id = self.auth.user_id()
        return ModelVersionList(
            self._search_model_versions(
                search_term=search_term,
                user_id=user_id,
                start=uploaded_time_start,
                end=uploaded_time_end,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
            )
        )

    def _search_my_model_versions(
        self,
        search_term: Optional[str] = None,
        uploaded_time_start: Optional["Datetime"] = None,
        uploaded_time_end: Optional["Datetime"] = None,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> ModelVersionList:
        """Search model versions owned by you.
            Example:
                >>> client.search_my_model_versions(search_term="my_model")
        :param search_term: Optional[str]: Searches the following metadata: names, shas, versions, file names, and tags
        :param uploaded_time_start: Optional["Datetime"]: Inclusive time of upload
        :param uploaded_time_end: Optional["Datetime"]: Inclusive time of upload
        :param workspace_id: Optional[int]: The workspace id to search in
        :param workspace_name: Optional[str]: The workspace name to search in
        :return: ModelVersionList
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        user_id = self.auth.user_id()
        return ModelVersionList(
            self._search_model_versions(
                search_term=search_term,
                user_id=user_id,
                start=uploaded_time_start,
                end=uploaded_time_end,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
            )
        )

    # TODO: Misleading name, this is actually searching for all model versions.
    # Future work will redo the query to give models instead of versions.
    def search_models(
        self,
        search_term: Optional[str] = None,
        uploaded_time_start: Optional["Datetime"] = None,
        uploaded_time_end: Optional["Datetime"] = None,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> ModelVersionList:
        """Search all models you have access to.
        :param search_term: Optional[str]: Searches the following metadata: names, shas, versions, file names, and tags
        :param uploaded_time_start: Optional[Datetime]: Inclusive time of upload
        :param uploaded_time_end: Optional[Datetime] Inclusive time of upload
        :param workspace_id: Optional[int]: The workspace id to search in
        :param workspace_name: Optional[str]: The workspace name to search in
        :return: ModelVersionList
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        return ModelVersionList(
            self._search_model_versions(
                search_term=search_term,
                start=uploaded_time_start,
                end=uploaded_time_end,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
            )
        )

    def search_model_versions(
        self,
        search_term: Optional[str] = None,
        uploaded_time_start: Optional["Datetime"] = None,
        uploaded_time_end: Optional["Datetime"] = None,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> ModelVersionList:
        """Search all model versions you have access to.
            Example:
                >>> client.search_model_versions(search_term="my_model")
        :param search_term: Optional[str]: Searches the following metadata: names, shas, versions, file names, and tags
        :param uploaded_time_start: Optional["Datetime"]: Inclusive time of upload
        :param uploaded_time_end: Optional["Datetime"]: Inclusive time of upload
        :param workspace_id: Optional[int]: The workspace id to search in
        :param workspace_name: Optional[str]: The workspace name to search in
        :return: ModelVersionList
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        return ModelVersionList(
            self._search_model_versions(
                search_term=search_term,
                start=uploaded_time_start,
                end=uploaded_time_end,
                workspace_id=workspace_id,
                workspace_name=workspace_name,
            )
        )

    def _search_model_versions(
        self,
        search_term=None,
        user_id=None,
        start=None,
        end=None,
        workspace_id=None,
        workspace_name=None,
    ) -> List[ModelVersion]:
        (query, params) = self._generate_model_query(
            search_term=search_term,
            user_id=user_id,
            start=start,
            end=end,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
        )

        q = gql.gql(query)

        data = self._gql_client.execute(q, variable_values=params)
        models = []
        if data["search_models"]:
            for m in data["search_models"]:
                models.append(ModelVersion(self, m))
        return models

    def _generate_model_query(
        self,
        search_term=None,
        user_id=None,
        start=None,
        end=None,
        workspace_id=None,
        workspace_name=None,
    ):
        filters = []
        query_params = []
        params = {}
        search = ""
        if search_term:
            search = search_term
        params["search_term"] = search
        query_params.append("$search_term: String!")

        self._add_filter_and_param_to_query(
            filters, params, query_params, "owner_id", "user_id", user_id, "String"
        )
        model_workspace_filtering = []
        self._add_workspace_filtering(
            model_workspace_filtering,
            params,
            query_params,
            workspace_id,
            workspace_name,
        )
        self._build_nested_query(filters, "model", model_workspace_filtering)

        self._generate_time_range_graphql(
            "created_at",
            start=start,
            end=end,
            filters=filters,
            params=params,
            query_params=query_params,
        )

        where_clause_str = self._generate_where_clause_str(filters)
        query_param_str = self._generate_query_param_str(query_params)
        query = f"""
            query GetModels({query_param_str}) {{
              search_models(args: {{search: $search_term}}{where_clause_str}, order_by: {{created_at: desc}}) {{
                id
              }}
            }}
        """
        return (query, params)

    def _add_workspace_filtering(
        self,
        filters: List[str],
        params: Dict[str, Any],
        query_params: List[str],
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ):
        if any([workspace_id, workspace_name]):
            workspace_filters: List[str] = []
            self._add_filter_and_param_to_query(
                workspace_filters,
                params,
                query_params,
                "id",
                "workspace_id",
                workspace_id,
                "bigint",
            )
            self._add_filter_and_param_to_query(
                workspace_filters,
                params,
                query_params,
                "name",
                "workspace_name",
                workspace_name,
                "String",
            )

            self._build_nested_query(filters, "workspace", workspace_filters)

    @staticmethod
    def _build_nested_query(
        filters: List[str], nested_field: str, nested_filters: List[str]
    ):
        if nested_filters:
            filter_length = len(nested_filters)
            if filter_length > 0:
                if filter_length > 1:
                    filters.append(
                        f"""{nested_field}: {{_and: [{", ".join(f"{{{fs}}}" for fs in nested_filters)}]}}"""
                    )
                else:
                    filters.append(f"{nested_field}: {{{nested_filters[0]}}}")

    @handle_errors()
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Find a user by email"""
        assert email is not None
        escaped_email = quote_plus(email)
        url = f"auth/admin/realms/master/users?email={escaped_email}"
        headers = {"Content-Type": "application/json"}
        resp = self.httpx_client.get(url, headers=headers)
        jresp = resp.json()
        return None if jresp == [] else User(client=self, data=jresp[0])

    @handle_errors()
    def deactivate_user(self, email: str) -> None:
        """Deactivates an existing user of the platform

        Deactivated users cannot log into the platform.
        Deactivated users do not count towards the number of allotted user seats from the license.

        The Models and Pipelines owned by the deactivated user are not removed from the platform.

        :param str email: The email address of the user to deactivate.

        :return: None
        :rtype: None
        """

        if self.auth.user_email() == email:
            raise Exception("A user may not deactive themselves.")

        user = self.get_user_by_email(email)

        if user is None:
            raise EntityNotFoundError("User", {"email": email})

        if user.username() == "admin":
            raise Exception("Admin user may not be deactivated.")

        url_path = f"auth/admin/realms/master/users/{user._id}"
        headers = {"Content-Type": "application/json"}
        # Get the current full user representation to return in the mutation due to keycloak bug
        get_user_response = self.httpx_client.get(url_path, headers=headers)

        cur_user_rep = get_user_response.json()
        cur_user_rep["enabled"] = False

        resp = self.httpx_client.put(url_path, headers=headers, json=cur_user_rep)

        if resp.status_code != 204:
            raise EntityNotFoundError("User", {"email": email})
        return None

    @handle_errors()
    def activate_user(self, email: str) -> None:
        """Activates an existing user of the platform that had been previously deactivated.

        Activated users can log into the platform.

        :param str email: The email address of the user to activate.

        :return: None
        :rtype: None
        """
        user = self.get_user_by_email(email)

        if user is None:
            raise EntityNotFoundError("User", {"email": email})

        url = f"auth/admin/realms/master/users/{user._id}"

        headers = {"Content-Type": "application/json"}
        # Get the current full user representation to return in the mutation due to keycloak bug
        get_user_response = self.httpx_client.get(url, headers=headers)

        cur_user_rep = get_user_response.json()
        cur_user_rep["enabled"] = True

        resp = self.httpx_client.put(url, headers=headers, json=cur_user_rep)

        if resp.status_code != 204:
            raise EntityNotFoundError("User", {"email": email})
        return None

    @handle_errors()
    def _get_user_by_id(self, id: str) -> Optional[User]:
        assert id is not None
        url = f"auth/admin/realms/master/users/{id}"
        headers = {"Content-Type": "application/json"}
        resp = self.httpx_client.get(url, headers=headers)
        if resp.status_code != 200:
            return None
        jresp = resp.json()
        return None if jresp == [] else User(client=self, data=jresp)

    def list_users(self) -> List[User]:
        """List of all Users on the platform

        :return: A list of all Users on the platform.
        :rtype: List[User]
        """
        resp = User.list_users(self)
        return [User(client=self, data=u) for u in resp]

    def upload_model(
        self,
        name: str,
        path: Union[str, pathlib.Path],
        framework: Optional[Framework] = None,
        input_schema: Optional[pa.Schema] = None,
        output_schema: Optional[pa.Schema] = None,
        convert_wait: Optional[bool] = True,
        arch: Optional[Architecture] = None,
        accel: Optional[Union[Acceleration, AccelerationWithConfig]] = None,
        framework_config: Optional[FrameworkConfig] = None,
    ) -> ModelVersion:
        """Upload a model defined by a file as a new model variant.

        :param name: str The name of the model of which this is a variant.
            Names must be ASCII alpha-numeric characters or dash (-) only.
        :param path: Union[str, pathlib.Path] Path of the model file to upload.
        :param framework: Optional[Framework] Supported model frameworks.
            Use models from Framework Enum. Example: Framework.PYTORCH, Framework.TENSORFLOW
        :param input_schema: Optional pa.Schema Input schema, required for flavors other than ONNX, Tensorflow, and Python
        :param output_schema: Optional pa.Schema Output schema, required for flavors other than ONNX, Tensorflow, and Python
        :param convert_wait: Optional bool Defaults to True. Specifies if method should return when conversion is over or not.
        :param framework_config: Optional FrameworkConfig, required for Framework.VLLM.
        :return: The created Model.
        :rtype: ModelVersion
        """
        require_dns_compliance(name)

        if not isinstance(framework, Framework):
            raise ValueError(
                "framework must be a Framework Enum. Example: Framework.PYTORCH, Framework.TENSORFLOW"
            )

        accel, arch, framework_config = self._apply_default_params_if_not_present(
            accel, arch, framework, framework_config
        )
        self._validate_accel(arch, accel)
        self._validate_framework_config(framework, framework_config)
        payload = self._prepare_base_payload_for_model_upload(name=name)

        if isinstance(path, str):
            path = pathlib.Path(path)

        with path.open("rb") as f:
            payload["conversion"] = self._get_conversion_params(
                framework,
                framework_config,
                arch,
                accel,
            )

            if framework in UPLOAD_MODEL_STREAM_SUPPORTED_FLAVORS:
                return self._upload_model_via_models_service(
                    payload, (path.name, f), False
                )

            payload.update(
                zip(
                    ["input_schema", "output_schema"],
                    self._get_serialized_schemas(input_schema, output_schema),
                )
            )

            return self._upload_model_via_models_service(
                payload, (path.name, f), True, convert_wait
            )

    def generate_upload_model_api_command(
        self,
        base_url: str,
        name: str,
        path: Union[str, pathlib.Path],
        framework: Optional[Framework] = None,
        input_schema: Optional[pa.Schema] = None,
        output_schema: Optional[pa.Schema] = None,
        arch: Optional[Architecture] = None,
        accel: Optional[Union[Acceleration, AccelerationWithConfig]] = None,
        framework_config: Optional[FrameworkConfig] = None,
    ) -> str:
        """Helper function to upload a large model via API in Wallaroo. It
        generates the equivalent CLI command to upload the model via API.

        :param base_url: str The base URL of the Wallaroo Cluster.
        :param name: str The name of the model of which this is a variant.
            Names must be ASCII alpha-numeric characters or dash (-) only.
        :param path: Union[str, pathlib.Path] Path of the model file to upload.
        :param framework: Optional[Framework] Supported model frameworks.
            Use models from Framework Enum. Example: Framework.PYTORCH, Framework.TENSORFLOW
        :param input_schema: Optional pa.Schema Input schema, required for flavors other than ONNX, Tensorflow, and Python
        :param output_schema: Optional pa.Schema Output schema, required for flavors other than ONNX, Tensorflow, and Python
        :param arch: Optional[Architecture] Supported architectures.
        :param accel: Optional[Acceleration] Supported types of acceleration.
        :param framework_config: Optional FrameworkConfig, required for Framework.VLLM.
        :return: The upload_and_convert CLI command.
        """
        if not isinstance(framework, Framework):
            raise ValueError(
                "framework must be a Framework Enum. Example: Framework.PYTORCH, Framework.TENSORFLOW"
            )

        accel, arch, framework_config = self._apply_default_params_if_not_present(
            accel, arch, framework, framework_config
        )
        self._validate_accel(arch, accel)
        self._validate_framework_config(framework, framework_config)
        payload = self._prepare_base_payload_for_model_upload(name=name)

        payload["conversion"] = self._get_conversion_params(
            framework,
            framework_config,
            arch,
            accel,
        )

        if framework not in UPLOAD_MODEL_STREAM_SUPPORTED_FLAVORS:
            payload.update(
                zip(
                    ["input_schema", "output_schema"],
                    self._get_serialized_schemas(input_schema, output_schema),
                )
            )

        return self._get_cli_cmd_for_model_upload(payload, path, base_url)

    def _get_cli_cmd_for_model_upload(
        self, payload: Dict[str, Any], path: Union[str, pathlib.Path], base_url: str
    ) -> str:
        base_url = base_url[:-1] if base_url.endswith("/") else base_url

        json_payload = json.dumps(payload)

        parts = [
            "curl --progress-bar -X POST",
            '-H "Content-Type: multipart/form-data"',
            f'-H "Authorization: Bearer {self.auth._access_token().token}"',
            f"-F 'metadata={json_payload};type=application/json'",
            f'-F "file=@{path};type=application/octet-stream"',
            f"{base_url}/v1/api/models/upload_and_convert",
        ]

        return " ".join(parts)

    @staticmethod
    def _get_serialized_schemas(
        input_schema: pa.Schema, output_schema: pa.Schema
    ) -> Tuple[str, str]:
        Client._check_if_schemas_present(
            input_schema=input_schema, output_schema=output_schema
        )
        return (
            Client._serialize_schema(schema=input_schema),
            Client._serialize_schema(schema=output_schema),
        )

    def _prepare_base_payload_for_model_upload(self, name: str) -> Dict[str, Any]:
        return {
            "name": name,
            "visibility": _Visibility.PRIVATE,
            "workspace_id": self.get_current_workspace().id(),
        }

    @staticmethod
    def _check_if_schemas_present(
        input_schema: Optional[pa.Schema], output_schema: Optional[pa.Schema]
    ) -> None:
        if input_schema is None:
            raise Exception("parameter 'input_schema' required for this framework")
        if output_schema is None:
            raise Exception("parameter 'output_schema' required for this framework")

    @staticmethod
    def _apply_default_params_if_not_present(
        accel: Optional[Union[Acceleration, AccelerationWithConfig]],
        arch: Optional[Architecture],
        framework: Framework,
        framework_config: Optional[FrameworkConfig],
    ) -> Tuple[
        Union[Acceleration, AccelerationWithConfig],
        Architecture,
        Optional[FrameworkConfig],
    ]:
        accel = accel or Acceleration.default()
        if isinstance(accel, Acceleration) and accel.requires_config():
            accel = accel.default_acceleration_with_config()

        arch = arch or Architecture.default()

        if framework_config is None:
            framework_config = framework.get_default_config()

        return accel, arch, framework_config

    @staticmethod
    def _get_conversion_params(
        framework: Framework,
        framework_config: Optional[FrameworkConfig],
        arch: Optional[Architecture],
        accel: Optional[Union[Acceleration, AccelerationWithConfig]],
    ) -> Dict[str, Any]:
        return {
            "arch": arch,
            "accel": accel.to_dict()
            if isinstance(accel, AccelerationWithConfig)
            else accel,
            "framework": framework.value,
            "framework_config": (
                framework_config.to_dict() if framework_config is not None else None
            ),
            "python_version": DEFAULT_MODEL_CONVERSION_PYTHON_VERSION,
            "requirements": [],
        }

    @staticmethod
    def _serialize_schema(schema: pa.Schema) -> str:
        return base64.b64encode(bytes(schema.serialize())).decode("utf8")

    @staticmethod
    def _validate_accel(
        arch: Optional[Architecture],
        accel: Optional[Union[Acceleration, AccelerationWithConfig]],
    ) -> None:
        if accel is not None:
            arch = arch or Architecture.default()
            if not accel.is_applicable(arch):
                raise InvalidAccelerationError()

    @staticmethod
    def _validate_framework_config(
        framework: Framework,
        framework_config: Optional[FrameworkConfig],
    ) -> None:
        framework.validate(framework_config)

    @handle_errors(ModelUploadError)
    def _upload_model_via_models_service(
        self,
        data: Dict[str, Any],
        file_info: Optional[Tuple[str, Any]],
        convert: Optional[bool] = True,
        convert_wait: Optional[bool] = True,
    ) -> ModelVersion:
        """
        Upload and (possibly) convert a model defined by a file as a new model variant. If convert_wait
        is True, the method will wait for about 10min for the conversion to finish before returning.
        If convert_wait is False, the method will return immediately.
        """
        files: Dict[str, Tuple[str | None, Any, str | None]] = {
            "metadata": (None, json.dumps(data), JSON_CONTENT_TYPE),
        }
        # we must have either file information or we're not trying to convert
        assert file_info is not None or convert is False
        if file_info is not None:
            filename = file_info[0]
            file = file_info[1]
            files["file"] = (filename, file, OCTET_STREAM_CONTENT_TYPE)

        route = "upload_and_convert" if convert else "upload"
        endpoint = f"/v1/api/models/{route}"

        self.auth._force_reload()

        res = self.httpx_client.post(endpoint, auth=self.auth, files=files)
        res.raise_for_status()
        try:
            res_dict = json.loads(res.text)
        except (json.JSONDecodeError, ValueError) as json_err:
            raise ValueError("Decoding response from model upload failed") from json_err

        model = ModelVersion(
            self, data=res_dict["insert_models"]["returning"][0]["models"][0]
        )
        if convert is not True or convert_wait is not True:
            return self._get_configured_model_version(model)
        else:
            return self._wait_for_model(model)

    def _write_line(self, message: str) -> None:
        """Helper to write a complete line with newline and flush."""
        sys.stdout.write(f"{message}\n")
        sys.stdout.flush()

    def _write_error(self, message: str) -> None:
        """Helper to write a complete line with newline and flush."""
        # Add red ANSI color formatting for error messages
        red_message = f"\033[91m{message}\033[0m"
        sys.stderr.write(f"{red_message}\n")
        sys.stderr.flush()

    def _write_progress(self, message: str) -> None:
        """Helper to write progress without newline and flush."""
        sys.stdout.write(message)
        sys.stdout.flush()

    def _wait_for_model(self, model_version: ModelVersion) -> ModelVersion:
        from .model_status import is_attempting_load, model_status_to_string
        from .wallaroo_ml_ops_api_client.models.model_status import ModelStatus

        poll_interval = 5
        expire_time = datetime.now() + timedelta(
            seconds=DEFAULT_MODEL_CONVERSION_TIMEOUT
        )
        last_status = None
        dots_printed = False
        conversion_error: Optional[Union[ModelConversionError, Exception]] = None
        timeout_error: Optional[ModelConversionTimeoutError] = None

        self._write_line("Waiting for model loading - this will take up to 10min.")

        try:
            while datetime.now() < expire_time:
                model_version = self._get_configured_model_version(model_version)
                status = model_version.status()

                # Handle status changes
                if last_status != status:
                    # Complete previous line if we were printing dots
                    if dots_printed:
                        self._write_line("")
                        dots_printed = False

                    # Print result of previous attempting state
                    if last_status is not None and is_attempting_load(last_status):
                        result = (
                            "Successful"
                            if status == ModelStatus.READY
                            else "Incompatible"
                        )
                        self._write_line(result)

                    # Handle terminal states
                    if status == ModelStatus.READY:
                        self._write_line("Ready")
                        return model_version
                    elif status == ModelStatus.ERROR:
                        self._write_error("ERROR!")
                        conversion_error = ModelConversionError(
                            "An error occurred during model conversion."
                        )
                        break

                    # Print new status
                    self._write_progress(f"Model is {model_status_to_string(status)}")
                    last_status = status
                else:
                    # Status unchanged - print progress dot
                    self._write_progress(".")
                    dots_printed = True

                time.sleep(poll_interval)
            else:
                # Timeout - complete current line
                if dots_printed:
                    self._write_line("")
                timeout_error = ModelConversionTimeoutError(
                    "Model conversion timed out after 10min."
                )

        except Exception as e:
            if dots_printed:
                self._write_line("")
            conversion_error = e

        try:
            model_version = self._get_configured_model_version(model_version)
        except Exception:
            pass

        if conversion_error:
            model_version._wait_error = conversion_error
        if timeout_error:
            model_version._wait_error = timeout_error

        if conversion_error or timeout_error:
            error_to_print = conversion_error or timeout_error
            error_message = (
                f"There was an error during model conversion: {error_to_print}"
            )
            self._write_error(error_message)
            # 2025.2 self._write_error("You can use model.upload_logs() to get more details.")
        return model_version

    @handle_errors()
    def _get_configured_model_version(
        self, model_version: ModelVersion
    ) -> ModelVersion:
        endpoint = "/v1/api/models/get_version_by_id"
        params = {"model_version_id": model_version.id()}
        get_model_version_response = self.httpx_client.post(
            endpoint, auth=self.auth, json=params
        )
        get_model_version_response.raise_for_status()
        try:
            get_model_version_response_dict = json.loads(
                get_model_version_response.text
            )
        except (json.JSONDecodeError, ValueError) as json_err:
            raise ValueError(
                "Decoding response from models/get_version_by_id failed"
            ) from json_err

        model_version = ModelVersion(
            self,
            data=get_model_version_response_dict["model_version"]["model_version"],
        )
        model_version._config = ModelConfig(
            self,
            get_model_version_response_dict["model_version"]["config"],
        )
        return model_version

    def register_model_image(self, name: str, image: str) -> ModelVersion:
        """Registers an MLFlow model as a new model.

        :param str model_name: The name of the model of which this is a variant.
            Names must be ASCII alpha-numeric characters or dash (-) only.
        :param str image: Image name of the MLFlow model to register.
        :return: The created Model.
        :rtype: ModelVersion
        """

        require_dns_compliance(name)
        data = {
            "image_path": image,
            "name": name,
            "visibility": _Visibility.PRIVATE,
            "workspace_id": self.get_current_workspace().id(),
            "conversion": {
                "framework": "mlflow",
                "python_version": DEFAULT_MODEL_CONVERSION_PYTHON_VERSION,
                "requirements": [],
            },
        }
        return self._upload_model_via_models_service(data, None, False)

    def get_model(self, name: str, version: Optional[str] = None):
        """
        Retrieves a model by name and optionally version from the current workspace.
        :param name: The name of the model.
        :param version: The version of the model. If not provided, the latest version is returned.
        :return ModelVersion: The requested model.
        Raises:
            Exception: If the model with the given name does not exist.
            Exception: If the model with the given version does not exist.
        """
        model = next(
            iter(
                [p for p in self.get_current_workspace().models() if p.name() == name]
            ),
            None,
        )
        if model is None:
            raise Exception(f"Error: A model with the name {name} does not exist.")
        if version is not None:
            model_version = next(
                iter([mv for mv in model.versions() if mv.version() == version]), None
            )
            if model_version is not None:
                return model_version
            else:
                raise Exception(
                    f"Error: A model with the version {version} not found in this workspace."
                )
        # workspaceById query brings model versions in descending order of updated_at
        return model.versions()[0]

    def model_by_name(
        self,
        name: str,
        version: str,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> ModelVersion:
        """Fetch a Model by name.

        :param name: str: Name of the model, same as model_id.
        :param version: str: Version string of the model
        :param workspace_id: Optional[int]: The workspace id to search in
        :param workspace_name: Optional[str]: The workspace name to search in
        :return: The Model with the corresponding model and variant name.
        :rtype: ModelVersion
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)

        model_by_name_query, params = self._generate_model_by_name_query(
            name, version, workspace_id, workspace_name
        )

        res = self._gql_client.execute(
            model_by_name_query,
            variable_values=params,
        )
        if not res["model"]:
            raise EntityNotFoundError(
                "ModelVersion", {"name": name, "model_version": version}
            )
        return ModelVersion(client=self, data={"id": res["model"][0]["id"]})

    def _generate_model_by_name_query(
        self,
        name: str,
        version: str,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ):
        filters: List[str] = []
        query_params: List[str] = []
        params: Dict[str, Any] = {}
        self._add_filter_and_param_to_query(
            filters, params, query_params, "model_id", "model_id", name, "String"
        )
        self._add_filter_and_param_to_query(
            filters,
            params,
            query_params,
            "model_version",
            "model_version",
            version,
            "String",
        )

        model_workspace_filtering: List[str] = []
        self._add_workspace_filtering(
            model_workspace_filtering,
            params,
            query_params,
            workspace_id,
            workspace_name,
        )
        if model_workspace_filtering:
            self._build_nested_query(filters, "model", model_workspace_filtering)

        where_clause_str = self._generate_where_clause_str(filters)
        query_param_str = self._generate_query_param_str(query_params)

        model_by_name_query = gql.gql(
            f"""
            query ModelByName({query_param_str}) {{
              model({where_clause_str}) {{
                id
                model_id
                model_version
              }}
            }}
            """
        )
        return model_by_name_query, params

    def model_version_by_name(self, model_class: str, model_name: str) -> ModelVersion:
        """Fetch a Model version by name.

        :param str model_class: Name of the model class.
        :param str model_name: Name of the variant within the specified model class.
        :return: The Model with the corresponding model and variant name.
        :rtype: ModelVersion
        """
        res = self._gql_client.execute(
            gql.gql(
                """
                query ModelByName($model_id: String!, $model_version: String!) {
                  model(where: {_and: [{model_id: {_eq: $model_id}}, {model_version: {_eq: $model_version}}]}) {
                    id
                    model_id
                    model_version
                  }
                }
                """
            ),
            variable_values={
                "model_id": model_class,
                "model_version": model_name,
            },
        )
        if not res["model"]:
            raise EntityNotFoundError(
                "ModelVersion", {"model_class": model_class, "model_name": model_name}
            )
        return ModelVersion(client=self, data={"id": res["model"][0]["id"]})

    def deployment_by_name(self, deployment_name: str) -> Deployment:
        """Fetch a Deployment by name.

        :param str deployment_name: Name of the deployment.
        :return: The Deployment with the corresponding name.
        :rtype: Deployment
        """
        res = self._gql_client.execute(
            gql.gql(
                """
                query DeploymentByName($deployment_name: String!) {
                  deployment(where: {deploy_id: {_eq: $deployment_name}}) {
                    id
                  }
                }
                """
            ),
            variable_values={
                "deployment_name": deployment_name,
            },
        )
        if not res["deployment"]:
            raise EntityNotFoundError(
                "Deployment", {"deployment_name": deployment_name}
            )
        return Deployment(client=self, data={"id": res["deployment"][0]["id"]})

    def pipelines_by_name(
        self,
        pipeline_name: str,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> List[Pipeline]:
        """Fetch Pipelines by name.

        :param str pipeline_name: Name of the pipeline.
        :param int workspace_id: ID of the workspace. Defaults to None.
        :param str workspace_name: Name of the workspace. Defaults to None.
        :return: The Pipeline with the corresponding name.
        :rtype: Pipeline
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)

        filters = []
        query_params = []
        params: Dict[str, Any] = {}
        filters.append("pipeline_id: {_eq: $pipeline_name}")
        params["pipeline_name"] = pipeline_name
        query_params.append("$pipeline_name: String!")

        if workspace_id:
            filters.append("workspace_id: {_eq: $workspace_id}")
            params["workspace_id"] = workspace_id
            query_params.append("$workspace_id: bigint!")
        if workspace_name:
            filters.append("workspace: {name: {_eq: $workspace_name}}")
            params["workspace_name"] = workspace_name
            query_params.append("$workspace_name: String!")

        where_clause_str = self._generate_where_clause_str(filters)
        query_param_str = self._generate_query_param_str(query_params)
        res = self._gql_client.execute(
            gql.gql(
                f"""
                query PipelineByName({query_param_str}) {{
                  pipeline({where_clause_str}, order_by: {{created_at: desc}}) {{
                    id
                    workspace {{
                        id
                        name
                    }}
                  }}
                }}
                """
            ),
            variable_values=params,
        )
        assert "pipeline" in res
        length = len(res["pipeline"])
        if length < 1:
            raise EntityNotFoundError("Pipeline", {"pipeline_name": pipeline_name})
        return Pipelines([Pipeline(client=self, data=p) for p in res["pipeline"]])

    def list_pipelines(
        self, workspace_id: Optional[int] = None, workspace_name: Optional[str] = None
    ) -> List[Pipeline]:
        """List all pipelines on the platform.
        :param int workspace_id: ID of the workspace. Defaults to None.
        :param str workspace_name: Name of the workspace. Defaults to None.
        :return: A list of all pipelines on the platform.
        :rtype: List[Pipeline]
        """
        from wallaroo.wallaroo_ml_ops_api_client.api.pipelines.list_pipelines import (
            ListPipelinesBody,
            sync,
        )

        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        res = sync(
            client=self.mlops(),
            body=ListPipelinesBody(
                workspace_id=workspace_id,
                workspace_name=workspace_name,
            ),
        )
        if res is None:
            raise Exception("Failed to list pipelines")
        return Pipelines(
            [Pipeline(client=self, data=d.pipeline.to_dict()) for d in res.pipelines]
        )

    def get_pipeline(self, name: str, version: Optional[str] = None) -> Pipeline:
        """
        Retrieves a pipeline by name and optional version from the current workspace.
        :param name: The name of the pipeline to retrieve.
        :param version: The version of the pipeline to retrieve. Defaults to None.
        :return: Pipeline: The requested pipeline.
        Raises:
            Exception: If the pipeline with the given name is not found in the workspace.
            Exception: If the pipeline with the given version is not found in the workspace.
        """
        pipeline = next(
            iter(
                [
                    p
                    for p in self.get_current_workspace().pipelines()
                    if p.name() == name
                ]
            ),
            None,
        )
        if pipeline is None:
            raise Exception(f"Pipeline {name} not found in this workspace.")
        if version is not None:
            pipeline_version = next(
                iter([pv for pv in pipeline.versions() if pv.name() == version]), None
            )
            if pipeline_version is not None:
                pipeline._pipeline_version_to_deploy = pipeline_version
                return pipeline
            else:
                raise Exception(
                    f"Pipeline version {version} not found in this workspace."
                )
        return pipeline

    def build_pipeline(self, pipeline_name: str) -> "Pipeline":
        """Starts building a pipeline with the given `pipeline_name`,
        returning a :py:PipelineConfigBuilder:

        When completed, the pipeline can be uploaded with `.upload()`

        :param pipeline_name string: Name of the pipeline, must be composed of ASCII
          alpha-numeric characters plus dash (-).
        """

        require_dns_compliance(pipeline_name)

        _Visibility.PRIVATE

        # TODO: Needs to handle visibility?
        data = pipelines_create.sync(
            client=self.mlops(),
            body=pipelines_create_body.PipelinesCreateBody(
                pipeline_name,
                self.get_current_workspace().id(),
                pipelines_create_body_definition_type_0.PipelinesCreateBodyDefinitionType0.from_dict(
                    {}
                ),
            ),
        )

        if data is None:
            raise Exception("Failed to create pipeline")

        if not isinstance(data, PipelinesCreateResponse200):
            raise Exception(data.msg)

        return Pipeline(client=self, data={"id": data.pipeline_pk_id})

    def _upload_pipeline_variant(
        self,
        name: str,
        config: PipelineConfig,
    ) -> Pipeline:
        """Creates a new PipelineVariant with the specified configuration.

        :param str name: Name of the Pipeline. Must be unique across all Pipelines.
        :param config PipelineConfig: Pipeline configuration.
        """
        definition = config.to_json()
        _Visibility.PRIVATE

        data = pipelines_create.sync(
            client=self.mlops(),
            body=pipelines_create_body.PipelinesCreateBody(
                name,
                self.get_current_workspace().id(),
                pipelines_create_body_definition_type_0.PipelinesCreateBodyDefinitionType0.from_dict(
                    definition
                ),
            ),
        )

        if data is None:
            # TODO: Generalize
            raise Exception("Failed to create pipeline")

        if not isinstance(data, PipelinesCreateResponse200):
            raise Exception(data.msg) if "msg" in data else Exception(data)

        pipeline_data = data.to_dict()
        pipeline_data["id"] = data.pipeline_pk_id

        return Pipeline(
            client=self,
            data=pipeline_data,
        )

    @staticmethod
    def _cleanup_arrow_data_for_display(arrow_data: pa.Table) -> pa.Table:
        """
        Cleans up the inference result and log data from engine / plateau for display (ux) purposes.
        """
        columns = []
        table_schema = []
        for column_name in arrow_data.column_names:
            column_data = arrow_data[column_name]
            column_schema = arrow_data.schema.field(column_name)
            if "time" == column_name:
                time_df = arrow_data["time"].to_pandas().copy()
                time_df = pd.to_datetime(time_df, unit="ms")
                column_data = pa.array(time_df)
                column_schema = pa.field("time", pa.timestamp("ms"))
            if "check_failures" == column_name:
                check_failures_df = arrow_data["check_failures"].to_pandas()
                column_data = pa.array(check_failures_df.apply(len))
                column_schema = pa.field("check_failures", pa.int8())
            columns.append(column_data)
            table_schema.append(column_schema)
        new_schema = pa.schema(table_schema)
        return pa.Table.from_arrays(columns, schema=new_schema)

    @staticmethod
    def _build_headers_and_params(
        limit: Optional[int] = None,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        headers = {"User-Agent": _user_agent}
        params = dict()
        headers.update({"Accept": ARROW_CONTENT_TYPE})
        if start_datetime is None and end_datetime is None:
            # type: ignore
            params["page_size"] = limit if limit is not None else DEFAULT_RECORDS_LIMIT
            params["order"] = "desc"  # type: ignore
        elif start_datetime is not None and end_datetime is not None:
            if limit is not None:
                params["page_size"] = limit  # type: ignore
            start_str = start_datetime.astimezone(tz=timezone.utc).isoformat()
            params["time.start"] = start_str  # type: ignore
            end_str = end_datetime.astimezone(tz=timezone.utc).isoformat()
            params["time.end"] = end_str  # type: ignore
        else:
            raise Exception(
                "Please provide both start datetime and end datetime together."
            )
        params["dataset[]"] = dataset or ["*"]  # type: ignore
        if dataset_exclude is not None:
            params["dataset.exclude[]"] = dataset_exclude  # type: ignore
        params["dataset.separator"] = dataset_separator or "."  # type: ignore

        return headers, params

    @handle_errors()
    def _get_next_records(
        self,
        params: Optional[Dict[str, Any]],
        iterator: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, Any]],
        base: str,
    ) -> httpx.Response:
        resp = self.httpx_client.post(
            base + "/records",
            params=params,
            json=iterator,
            headers=headers,
        )
        resp.raise_for_status()
        return resp

    def _extract_logs_from_response(
        self, resp: httpx.Response
    ) -> Tuple[pa.Table, Dict[str, Any], str]:
        with pa.ipc.open_file(resp.content) as reader:
            entries = reader.read_all()
            metadata_dict = reader.schema.metadata
            metadata = (
                json.loads(metadata_dict[b"status"])
                if metadata_dict is not None
                else None
            )
            status = metadata["status"] if metadata is not None else None
            if entries.num_rows > 0:
                clean_entries = self._cleanup_arrow_data_for_display(entries)
                iterator = metadata["next"] if "next" in metadata else None
                return clean_entries, iterator, status
            else:
                iterator = None
                return entries, iterator, status

    @staticmethod
    def _slice_log_results_if_exceeds_limit(
        logs_table: pa.Table, rows_written: int, limit: Optional[int] = None
    ) -> Tuple[pa.Table, int, bool]:
        if limit is not None and rows_written >= limit:
            return (
                logs_table.slice(0, limit - (rows_written - logs_table.num_rows)),
                limit,
                True,
            )
        return logs_table, rows_written, False

    @staticmethod
    def _should_stop_log_collection(
        status: str,
        data_size_exceeded: bool,
        rows_written: int,
        end_time: str,
        data_size: float,
        data_unit: DataSizeUnit,
        is_sliced: bool,
        chronological_order: str,
    ) -> bool:
        if data_size_exceeded:
            sys.stderr.write(
                f"Warning: Pipeline log data size limit of {data_size} {data_unit.value} exceeded."
                f" {rows_written} {chronological_order} records exported successfully, {chronological_order}"
                f" record seen was at {end_time}. Set a different limit using data_size_limit for more data."
                f" Please request additional files separately.\n\n"
            )
            return True
        if status == "RecordLimited":
            sys.stderr.write(
                "Warning: There are more logs available."
                " Please set a larger limit to export more data.\n\n"
            )
            return True
        if status == "All":
            return True
        if is_sliced:
            return True

        return False

    def _process_logs(
        self, logs_table: pa.Table, rows_written: int, limit: Optional[int]
    ) -> Tuple[pa.Table, int, bool, str]:
        rows_written += logs_table.num_rows
        (
            logs_table,
            total_rows_written,
            is_sliced,
        ) = self._slice_log_results_if_exceeds_limit(logs_table, rows_written, limit)
        end_time = (
            logs_table.column("time")[-1].as_py() if logs_table.num_rows > 0 else None
        )
        return logs_table, total_rows_written, is_sliced, end_time

    @staticmethod
    def _validate_file_size_input(data_size_limit: str) -> Tuple[float, DataSizeUnit]:
        pattern = r"^(\d+(\.\d+)?)\s*([KMGT]iB)$"
        match = re.match(pattern, data_size_limit, re.IGNORECASE)

        if not match:
            raise ValueError(
                "Invalid data size format. Please use the format: <number><unit> (e.g. 1.5MiB or 1 GiB)"
            )

        size = float(match.group(1))
        unit = DataSizeUnit.from_string(match.group(3).strip())

        if size <= 0:
            raise ValueError("File size must be positive.")

        return size, unit

    def _export_logs(
        self,
        base: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
        directory: str,
        file_prefix: str,
        data_size_limit: Optional[str] = None,
        limit: Optional[int] = None,
        arrow: Optional[bool] = False,
    ) -> None:
        iterator = {}  # type: Dict[str, Any]

        chronological_order = (
            "oldest" if "time.start" and "time.end" in params else "newest"
        )
        data_size, data_unit = (
            self._validate_file_size_input(data_size_limit)
            if data_size_limit
            else (DEFAULT_MAX_DATA_SIZE, DEFAULT_MAX_DATA_UNIT)
        )
        data_size_limit_in_bytes = data_unit.calculate_bytes(data_size)

        rows_written = 0
        writer = None
        file_num = 0
        schema = None
        schema_changed = False
        columns_dropped = False
        end_time = None
        previous_end_time = None
        data_size_exceeded = False
        total_arrow_data_size = 0
        total_pandas_data_size = 0
        dropped_columns = []
        while iterator is not None:
            response = self._get_next_records(params, iterator, headers, base)
            logs_table, iterator, status = self._extract_logs_from_response(response)
            if logs_table.num_rows == 0:
                break
            if "metadata.dropped" in logs_table.column_names:
                flattened_metadata = logs_table["metadata.dropped"].flatten()
                if len(flattened_metadata[0][0]) > 0:
                    columns_dropped = True
                    dropped_columns = flattened_metadata[0][0]
            if "metadata" not in params["dataset[]"]:
                metadata_columns_to_drop = []
                for column_name in logs_table.column_names:
                    if column_name.startswith("metadata."):
                        metadata_columns_to_drop.append(column_name)
                logs_table = logs_table.drop(metadata_columns_to_drop)
            if schema is not None and schema != logs_table.schema:
                schema_changed = True
                writer.close()
                writer = None
            if writer is None:
                schema = logs_table.schema
                file_num += 1
                writer = create_new_file(
                    directory, file_num, file_prefix, schema, arrow
                )

            if end_time is None:
                previous_end_time = logs_table.column("time")[-1].as_py()

            sliced_table, rows_written, is_sliced, sliced_end_time = self._process_logs(
                logs_table, rows_written, limit
            )

            end_time = (
                sliced_end_time if sliced_end_time is not None else previous_end_time
            )
            for record_batch in sliced_table.to_batches():
                if arrow:
                    total_arrow_data_size += record_batch.nbytes
                    write_to_file(record_batch, writer)
                    if total_arrow_data_size > data_size_limit_in_bytes:
                        data_size_exceeded = True
                        break
                else:
                    json_str = record_batch.to_pandas().to_json(
                        orient="records", lines=True
                    )
                    total_pandas_data_size += sys.getsizeof(json_str)
                    write_to_file(json_str, writer)
                    if total_pandas_data_size > data_size_limit_in_bytes:
                        data_size_exceeded = True
                        break

            if self._should_stop_log_collection(
                status,
                data_size_exceeded,
                rows_written,
                end_time,
                data_size,
                data_unit,
                is_sliced,
                chronological_order,
            ):
                writer.close()
                break
        if schema_changed:
            sys.stderr.write(
                "Note: The logs with different schemas are "
                "written to separate files in the provided directory."
            )
        if columns_dropped:
            sys.stderr.write(
                f"Warning: The inference log is above the allowable limit and the following columns may have"
                f" been suppressed for various rows in the logs: {dropped_columns}."
                f" To review the dropped columns for an individual inference's suppressed data,"
                f' include dataset=["metadata"] in the log request.'
                f"\n"
            )
        return None

    def get_logs(
        self,
        topic: str,
        limit: Optional[int] = None,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
        directory: Optional[str] = None,
        file_prefix: Optional[str] = None,
        data_size_limit: Optional[str] = None,
        arrow: Optional[bool] = False,
    ) -> Tuple[Union[pa.Table, pd.DataFrame, None], Optional[str]]:
        """
        Get logs for the given topic.
        :param topic: str The topic to get logs for.
        :param limit: Optional[int] The maximum number of logs to return.
        :param start_datetime: Optional[datetime] The start time to get logs for.
        :param end_datetime: Optional[datetime] The end time to get logs for.
         :param dataset: Optional[List[str]] By default this is set to ["*"] which returns,
            ["time", "in", "out", "anomaly"]. Other available options - ["metadata"]
        :param dataset_exclude: Optional[List[str]] If set, allows user to exclude parts of dataset.
        :param dataset_separator: Optional[Union[Sequence[str], str]] If set to ".", return dataset will be flattened.
        :param directory: Optional[str] If set, logs will be exported to a file in the given directory.
        :param file_prefix: Optional[str] Prefix to name the exported file. Required if directory is set.
        :param data_size_limit: Optional[str] The maximum size of the exported data in MB.
            Size includes all files within the provided directory. By default, the data_size_limit will be set to 100MB.
        :param arrow: Optional[bool] If set to True, return logs as an Arrow Table. Else, returns Pandas DataFrame.
        :return: Tuple[Union[pa.Table, pd.DataFrame], str] The logs and status.
        """
        base = "/v1/logs/topic/" + topic

        headers, params = self._build_headers_and_params(
            limit=limit,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            dataset=dataset,
            dataset_exclude=dataset_exclude,
            dataset_separator=dataset_separator,
        )
        if file_prefix is not None and directory is not None:
            self._export_logs(
                base=base,
                directory=directory,
                file_prefix=file_prefix,
                data_size_limit=data_size_limit,
                params=params,
                headers=headers,
                limit=limit,
                arrow=arrow,
            )
            return None, None
        response = self._get_next_records(
            params=params, iterator={}, headers=headers, base=base
        )
        entries, _, status = self._extract_logs_from_response(response)
        return entries if arrow else entries.to_pandas(), status

    def get_raw_logs(
        self,
        topic: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100_000,
        dataset: Optional[List[str]] = None,
        dataset_exclude: Optional[List[str]] = None,
        dataset_separator: Optional[str] = None,
        verbose: bool = False,
    ) -> Union[List[Dict[str, Any]], pd.DataFrame]:
        """
        Gets logs from Plateau for a particular time window.
        :param topic: str The name of the topic to query
        :param start: Optional[datetime] The start of the time window
        :param end: Optional[datetime] The end of the time window
        :param limit: int The number of records to retrieve. Note retrieving many
            records may be a performance bottleneck.
        :param verbose: bool Prints out info to help diagnose issues.
        :return: List[Dict[str, Any]], pd.DataFrame The logs from given time window.
        """

        assert limit <= 1_000_000

        base = "/v1/logs/topic/" + topic
        resp = self.httpx_client.get(base, auth=self.auth)
        if resp.status_code != 200:
            raise EntityNotFoundError(
                f"Could not get partitions {resp.text}", {"url": base}
            )
        data = resp.json()
        partitions = data["partitions"]

        if verbose:
            print(f"Got partitions {partitions}")

        params: Dict[str, Any] = {"page_size": limit}
        if start is not None:
            start_str = start.astimezone(tz=timezone.utc).isoformat()
            params["time.start"] = start_str
        if end is not None:
            end_str = end.astimezone(tz=timezone.utc).isoformat()
            params["time.end"] = end_str

        if len(partitions) == 0:
            next: Optional[Dict[str, int]] = None
        else:
            sizes = [
                sz + excess
                for sz, excess in zip(
                    repeat(limit // len(partitions), len(partitions)),
                    chain(repeat(1, limit % len(partitions)), repeat(0)),
                )
            ]

            next = {
                k: max(0, span["end"] - sz)
                for (k, span), sz in zip(partitions.items(), sizes)
            }

        headers = {"Accept": ARROW_CONTENT_TYPE}
        params["dataset[]"] = dataset or ["*"]
        if dataset_exclude is not None:
            params["dataset.exclude[]"] = dataset_exclude
        if dataset_separator is not None:
            params["dataset.separator"] = dataset_separator  # type: ignore

        if verbose:
            print("Using params: ", params)
            print("Using iterators: ", next)

        records = []
        while next is not None:
            resp = self.httpx_client.post(
                base + "/records",
                params=params,
                json=next,
                auth=self.auth,
                headers=headers,
            )
            if resp.status_code != 200:
                raise EntityNotFoundError(
                    f"Could not get records {resp.text}",
                    {"url": base, "params": str(params), "iterator": str(next)},
                )

            if verbose:
                print("response: ", resp)

            with pa.ipc.open_file(resp.content) as reader:
                entries_df = reader.read_pandas()
                if len(entries_df) > 0:
                    records.append(entries_df)
                    next = json.loads(reader.schema.metadata[b"status"])["next"]
                else:
                    next = None

        return pd.concat(records) if len(records) > 0 else pd.DataFrame()

    def get_raw_pipeline_inference_logs(
        self,
        topic: str,
        start: datetime,
        end: datetime,
        model_name: Optional[str] = None,
        limit: int = 100_000,
        verbose: bool = False,
    ) -> List[Union[Dict[str, Any], pd.DataFrame]]:
        """
        Gets logs from Plateau for a particular time window and filters them for
        the model specified.
        :param pipeline_name: The name/pipeline_id of the pipeline to query
        :param topic: The name of the topic to query
        :param start: The start of the time window
        :param end: The end of the time window
        :param model_id: The name of the specific model to filter if any
        :param limit: The number of records to retrieve. Note retrieving many
            records may be a performance bottleneck.
        :param verbose: Prints out info to help diagnose issues.
        :return: The raw logs from given time window anf filtered by model_name.
        """
        logs = self.get_raw_logs(
            topic,
            start=start,
            end=end,
            limit=limit,
            verbose=verbose,
        )

        if verbose:
            print(f"Got {len(logs)} initial logs")

        if len(logs) == 0:
            return logs

        if model_name:
            if isinstance(logs, pd.DataFrame):
                logs = logs[
                    logs["metadata"].map(
                        lambda md: json.loads(md["last_model"])["model_name"]
                    )
                    == model_name
                ]
            else:
                logs = [log for log in logs if log["model_name"] == model_name]

        # inference results are a unix timestamp in millis - filter by that
        start_ts = int(start.timestamp() * 1000)
        end_ts = int(end.timestamp() * 1000)

        if isinstance(logs, pd.DataFrame):
            logs = logs[(start_ts <= logs["time"]) & (logs["time"] < end_ts)]
        else:
            logs = [log for log in logs if start_ts <= log["time"] < end_ts]

        return logs

    def get_pipeline_inference_dataframe(
        self,
        topic: str,
        start: datetime,
        end: datetime,
        model_name: Optional[str] = None,
        limit: int = 100_000,
        verbose=False,
    ) -> pd.DataFrame:
        logs = self.get_raw_pipeline_inference_logs(
            topic, start, end, model_name, limit, verbose
        )
        if isinstance(logs, pd.DataFrame):
            return nested_df_to_flattened_df(logs)

        return inference_logs_to_dataframe(logs)

    def get_assay_results(
        self,
        assay_id: Union[str, int],
        start: datetime,
        end: datetime,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> IAssayAnalysisList:
        """Gets the assay results for a particular time window, parses them, and returns an
        List of AssayAnalysis.
        :param assay_id: int The id of the assay we are looking for.
        :param start: datetime The start of the time window. If timezone info not set, uses UTC timezone by default.
        :param end: datetime The end of the time window. If timezone info not set, uses UTC timezone by default.
        :param workspace_id: Optional[int] The id of the workspace to retrieve the assay from.
        :param workspace_name: Optional[str] The name of the workspace to retrieve the assay from.
        :return: List[IAssayAnalysis] The assay results for the given time window.
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        # We don't need the assays v2 flag here. Leaving it out ensures compatibility if it's not enabled.
        if isinstance(assay_id, str):
            return AssayV2(self, id=assay_id).results(
                start=start, end=end, workspace_id=workspace_id
            )

        res = assays_get_assay_results.sync(
            client=self.mlops(),
            body=assays_get_assay_results_body.AssaysGetAssayResultsBody(
                assay_id,
                _ensure_tz(start),
                _ensure_tz(end),
                workspace_id,
                workspace_name,
            ),
        )

        if res is None:
            raise Exception("Failed to list models")

        if not isinstance(res, List):
            raise Exception(res.msg)

        if len(res) != 0 and not isinstance(
            res[0], AssaysGetAssayResultsResponse200Item
        ):
            raise Exception("invalid response")
        return AssayAnalysisList(
            [AssayAnalysis(client=self, raw=v.to_dict()) for v in res]
        )

    def build_assay(
        self,
        *,
        assay_name: str,
        pipeline: Pipeline,
        iopath: str,
        model_name: Optional[str] = None,
        baseline_start: Optional[datetime] = None,
        baseline_end: Optional[datetime] = None,
        baseline_data: Optional[np.ndarray] = None,
    ) -> AssayBuilder:
        """Creates an AssayBuilder that can be used to configure and create
        Assays.
        :param assay_name: str Human friendly name for the assay
        :param pipeline: Pipeline The pipeline this assay will work on
        :param iopath: str The path to the input or output of the model that this assay will monitor.
        :param model_name: Optional[str] The name of the model to use for the assay.
        :param baseline_start: Optional[datetime] The start time for the inferences to
            use as the baseline
        :param baseline_end: Optional[datetime] The end time of the baseline window.
        the baseline. Windows start immediately after the baseline window and
        are run at regular intervals continuously until the assay is deactivated
        or deleted.
        :param baseline_data: Optional[np.ndarray] Use this to load existing baseline data at assay creation time.
        """
        assay_builder = AssayBuilder(
            client=self,
            name=assay_name,
            pipeline_id=pipeline.id(),
            pipeline_name=pipeline.name(),
            model_name=model_name,
            iopath=iopath,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            baseline_data=baseline_data,
        )

        return assay_builder

    def upload_assay(self, config: AssayConfig) -> Union[int, str]:
        """Creates an assay in the database.
        :param config AssayConfig: The configuration for the assay to create.
        :return assay_id: The identifier for the assay that was created.
        :rtype Union[int, str] - int for v1 API, str for v2 API
        """

        if is_assays_v2_enabled():
            return self._schedule_assay_v2_from_v1(config).id

        data = assays_create.sync(
            client=self.mlops(),
            body=AssaysCreateBody.from_dict(
                {
                    **json.loads(config.to_json()),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            ),
        )

        if data is None:
            raise Exception("Failed to create assay")

        if not isinstance(data, AssaysCreateResponse200):
            raise Exception(data)

        return data.assay_id

    def list_assays(
        self, workspace_id: Optional[int] = None, workspace_name: Optional[str] = None
    ) -> List[Assay]:
        """List all assays on the platform.
        :param workspace_id: Optional[int] The identifier for the workspace to retrieve the assays from.
        :param workspace_name: Optional[str] The name of the workspace to retrieve the assays from.
        :return: A list of all assays on the platform, unless filtered by workspace.
        :rtype: List[Assay]
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        if is_assays_v2_enabled():
            return self._list_assays_v2(workspace_id, workspace_name)

        list_assays_request_dict = {
            "workspace_id": workspace_id,
            "workspace_name": workspace_name,
        }
        res = assays_list.sync(
            client=self.mlops(), body=AssaysListBody.from_dict(list_assays_request_dict)
        )

        if res is None:
            raise Exception("Failed to get assays")

        if not isinstance(res, List):
            raise Exception(res.msg)

        return Assays([Assay(client=self, data=v.to_dict()) for v in res])

    def get_assay_info(
        self,
        assay_id: Union[int, str],
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> pd.DataFrame:
        """Get information about a specific assay.

        :param assay_id: int The identifier for the assay to retrieve.
        :param workspace_id: Optional[int] The identifier for the workspace to retrieve the assay from.
        :param workspace_name: Optional[str] The name of the workspace to retrieve the assay from.
        :return: The assay with the given identifier
        :rtype: Assay
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        if isinstance(assay_id, str):
            workspace_id = self._get_id_for_workspace(workspace_id, workspace_name)
            assay = AssayV2(self, id=assay_id)
            # If workspace_id is None, we don't need to check if the assay is in the workspace
            if (
                workspace_id is None
                or workspace_id == assay.targeting.data_origin.workspace_id
            ):
                return assay
            else:
                raise Exception("Assay not found in the workspace")

        return Assay.get_assay_info(
            client=self,
            assay_id=assay_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
        )

    def set_assay_active(self, assay_id: Union[int, str], active: bool) -> None:
        """Sets the state of an assay to active or inactive.

        :param assay_id: int The id of the assay to set the active state of.
        :param active: bool The active state to set the assay to. Default is True.
        """
        if isinstance(assay_id, str):
            _ = AssayV2(self, assay_id).set_active(active)
            return

        res = assays_set_active.sync(
            client=self.mlops(),
            body=AssaysSetActiveBody(assay_id, active),
        )

        if res is None:
            raise Exception("Failed to set assay active")

        if not isinstance(res, AssaysSetActiveResponse200):
            raise Exception(res.msg)

    def _list_assays_v2(
        self, workspace_id: Optional[int] = None, workspace_name: Optional[str] = None
    ):
        from .wallaroo_ml_ops_api_client.api.assays.get import GetBody, sync
        from .wallaroo_ml_ops_api_client.models.filter_on_active import FilterOnActive

        workspace_id = self._get_id_for_workspace(workspace_id, workspace_name)
        ret = sync(
            client=self.mlops(),
            body=GetBody(active=FilterOnActive.ALL, workspace_id=workspace_id),
        )
        if ret is None:
            raise Exception("Failed to get assays")
        return AssayV2List([AssayV2(client=self, id=str(x.id)) for x in ret])

    def _schedule_assay_v2_from_v1(
        self,
        config: AssayConfig,
    ):
        name = config.name
        config_summarizer = cast(UnivariateContinousSummarizerConfig, config.summarizer)

        baseline = cast(Union[None, SummaryBaseline, V2StaticBaseline], None)
        # TODO: if baseline.start is specified, send to assays v2 instead of using computed.
        baseline_end_at = cast(Optional[datetime], None)

        # Targeting
        targeting = Targeting._from_v1_config(config)
        iopath = targeting._get_iopath()

        if isinstance(config.baseline, V1CalculatedBaseline) or isinstance(
            config.baseline, V1FixedBaseline
        ):
            end = cast(str, config.baseline.calculated["fixed_window"].get("end_at"))
        elif isinstance(config.baseline, V1StaticBaseline):
            end = cast(str, config.baseline.static.get("end"))
            baseline = SummaryBaseline.from_v1_summary(
                config.baseline, config_summarizer, iopath
            )

        if end is not None:
            baseline_end_at = dateutil.parser.parse(end)

        if baseline is None:
            raise Exception("Failed to parse Baseline from v1 config")

        # Scheduling
        # if interval is None, legacy behavior is to be the same as width.
        interval = (
            config.window.interval if config.window.interval else config.window.width
        )

        first_run = (
            config.window.start
            if config.window.start
            else (baseline_end_at if baseline_end_at else datetime.now(timezone.utc))
        )

        run_frequency = cast(Optional[PGInterval], None)
        [count, unit] = interval.split()
        if unit == "minutes" or unit == "minute":
            run_frequency = PGInterval(quantity=int(count), unit=IntervalUnit.MINUTE)
        elif unit == "hours" or unit == "hour":
            run_frequency = PGInterval(quantity=int(count), unit=IntervalUnit.HOUR)
        elif unit == "days" or unit == "day":
            run_frequency = PGInterval(quantity=int(count), unit=IntervalUnit.DAY)
        elif unit == "weeks" or unit == "week":
            run_frequency = PGInterval(quantity=int(count), unit=IntervalUnit.WEEK)

        if run_frequency is None:
            raise Exception(
                "Failed to parse the run frequency for this assay.", interval
            )

        sched = Scheduling(
            first_run=first_run,
            run_frequency=RunFrequencyType1(simple_run_frequency=run_frequency),
            end=config.run_until,
        )

        # Window - Convert width to seconds
        dur = None
        [count, unit] = config.window.width.split()
        if unit == "minutes" or unit == "minute":
            dur = int(count) * 60
        elif unit == "hours" or unit == "hour":
            dur = int(count) * 60 * 60
        elif unit == "days" or unit == "day":
            dur = int(count) * 60 * 60 * 24
        elif unit == "weeks" or unit == "week":
            dur = int(count) * 60 * 60 * 24 * 7

        window = RollingWindow(width=WindowWidthDuration(seconds=_unwrap(dur)))

        # Summarizer
        summarizer = Summarizer.from_v1_summarizer(config_summarizer)

        ret = sync(
            client=self.mlops(),
            body=ScheduleBody(
                name=name,
                baseline=baseline,
                scheduling=sched,
                summarizer=summarizer,
                targeting=targeting,
                window=window,
            ),
        )

        if ret.parsed is None:
            raise Exception("Failed to create V2 assay from a V1 config.", ret)

        return AssayV2(client=self, id=str(ret.parsed))

    def create_tag(self, tag_text: str) -> Tag:
        """Create a new tag with the given text."""
        assert tag_text is not None
        return Tag._create_tag(client=self, tag_text=tag_text)

    def create_workspace(self, workspace_name: str) -> Workspace:
        """Create a new workspace with the current user as its first owner.

        :param str workspace_name: Name of the workspace, must be composed of ASCII
           alpha-numeric characters plus dash (-)"""
        assert workspace_name is not None
        require_dns_compliance(workspace_name)
        return Workspace._create_workspace(client=self, name=workspace_name)

    def list_workspaces(self) -> List[Workspace]:
        """List all workspaces on the platform which this user has permission see.

        :return: A list of all workspaces on the platform.
        :rtype: List[Workspace]
        """
        return Workspace.list_workspaces(self)

    def get_workspace(
        self, name: str, create_if_not_exist: Optional[bool] = False
    ) -> Optional[Workspace]:
        """
        Get a workspace by name. If the workspace does not exist, create it.
        :param name: The name of the workspace to get.
        :param create_if_not_exist: If set to True, create a new workspace if workspace by given name doesn't already exist.
            Set to False by default.
        :return: The workspace with the given name.
        """
        return Workspace.get_workspace(
            client=self, name=name, create_if_not_exist=create_if_not_exist
        )

    def set_current_workspace(self, workspace: Workspace) -> Workspace:
        """Any calls involving pipelines or models will use the given workspace from then on."""
        assert workspace is not None
        if not isinstance(workspace, Workspace):
            raise TypeError("Workspace type was expected")

        self._current_workspace = workspace
        return cast("Workspace", self._current_workspace)

    def get_current_workspace(self) -> Workspace:
        """Return the current workspace.  See also `set_current_workspace`."""
        if self._current_workspace is None:
            # Is there a default? Use that or make one.
            default_ws = Workspace._get_user_default_workspace(self)
            if default_ws is not None:
                self._current_workspace = default_ws
            else:
                self._current_workspace = Workspace._create_user_default_workspace(self)

        return cast("Workspace", self._current_workspace)

    def invite_user(self, email, password=None):
        return User.invite_user(self, email, password)

    def get_topic_name(self, pipeline_pk_id: int) -> str:
        return self.httpx_client.post(
            "v1/api/plateau/get_topic_name",
            json={"pipeline_pk_id": pipeline_pk_id},
        ).json()["topic_name"]

    def list_orchestrations(
        self, workspace_id: Optional[int] = None, workspace_name: Optional[str] = None
    ) -> List[Orchestration]:
        """List all Orchestrations in the current workspace.
        :param workspace_id: Optional[int] The ID of the workspace to list Orchestrations from.
        :param workspace_name: Optional[str] The name of the workspace to list Orchestrations from.
        :return: A List containing all Orchestrations in the current workspace.
        """
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        workspace_id = self._get_id_for_workspace(workspace_id, workspace_name)
        return Orchestration.list_orchestrations(self, workspace_id)

    def upload_orchestration(
        self,
        bytes_buffer: Optional[bytes] = None,
        path: Optional[str] = None,
        name: Optional[str] = None,
        file_name: Optional[str] = None,
    ):
        """Upload a file to be packaged and used as an Orchestration.

        The uploaded artifact must be a ZIP file which contains:

        * User code. If `main.py` exists, then that will be used as the task entrypoint. Otherwise,
          the first `main.py` found in any subdirectory will be used as the entrypoint.
        * Optional: A standard Python `requirements.txt` for any dependencies to be provided in the
          task environment. The Wallaroo SDK will already be present and should not be mentioned.
          Multiple `requirements.txt` files are not allowed.
        * Optional: Any other artifacts desired for runtime, including data or code.

        :param Optional[str] path: The path to the file on your filesystem that will be uploaded as an Orchestration.
        :param Optional[bytes] bytes_buffer: The raw bytes to upload to be used Orchestration. Cannot be used with the `path` param.
        :param Optional[str] name: An optional descriptive name for this Orchestration.
        :param Optional[str] file_name: An optional filename to describe your Orchestration when using the bytes_buffer param. Ignored when `path` is used.
        :return: The Orchestration that was uploaded.
        :raises OrchestrationUploadFailed If a server-side error prevented the upload from succeeding.

        """
        return Orchestration.upload(
            self, bytes_buffer=bytes_buffer, path=path, name=name, file_name=file_name
        )

    def list_tasks(
        self,
        killed: bool = False,
        workspace_id: Optional[int] = None,
        workspace_name: Optional[str] = None,
    ) -> List[Task]:
        """List all Tasks in the current Workspace.
        :param killed: bool If set to True, list all killed tasks.
        :param workspace_id: Optional[int] The ID of the workspace to list Tasks from.
        :param workspace_name: Optional[str] The name of the workspace to list Tasks from.
        :return: A List containing Task objects."""
        self._validate_workspace_id(workspace_id)
        self._validate_workspace_name(workspace_name)
        workspace_id = self._get_id_for_workspace(workspace_id, workspace_name)
        return Task.list_tasks(self, killed=killed, workspace_id=workspace_id)

    def get_task_by_id(self, task_id: str):
        """Retrieve a Task by its ID.

        :param str task_id: The ID of the Task to retrieve.
        :return: A Task object."""
        return Task.get_task_by_id(self, task_id)

    def in_task(self) -> bool:
        """Determines if this code is inside an orchestration task.

        :return: True if running in a task."""
        return self._in_task

    def task_args(self) -> Dict[Any, Any]:
        """When running inside a task (see `in_task()`), obtain arguments passed to the task.

        :return: Dict of the arguments"""
        with open(self._task_args_filename, "rb") as fp:
            return json.load(fp)

    def list_connections(self) -> ConnectionList:
        """List all Connections defined in the platform.
        :return: List of Connections in the whole platform.
        """
        return Connection.list_connections(self)

    def get_connection(self, name=str) -> Connection:
        """Retrieves a Connection by its name.
        :return: Connection to an external data source.
        """
        return Connection.get_connection(self, name=name)

    def create_connection(
        self, name=str, connection_type=str, details=Dict[str, Any]
    ) -> Connection:
        """Creates a Connection with the given name, type, and type-specific details.
        :return: Connection to an external data source.
        """
        return Connection.create_connection(
            self, name=name, connection_type=connection_type, details=details
        )

    def create_model_registry(
        self, name: str, token: str, url: str, workspace_id: Optional[int] = None
    ) -> ModelRegistry:
        """Create a Model Registry connection in this workspace that can be reused across workspaces.

        :param name str A descriptive name for this registry
        :param token str A Bearer token necessary for accessing this Registry.
        :param url str The root URL for this registry. It should NOT include `/api/2.0/mlflow` as part of it.
        :param workspace_id int The ID of the workspace to attach this registry to, i.e. `client.get_current_workspace().id()`.
        :return: A ModelRegistry object.
        """
        from .wallaroo_ml_ops_api_client.api.model.create_registry import (
            CreateRegistryWithoutWorkspaceRequest,
            sync_detailed as sync,
        )

        ret = sync(
            client=self.mlops(),
            body=CreateRegistryWithoutWorkspaceRequest(
                name=name,
                token=token,
                url=url,
                workspace_id=workspace_id,
            ),
        )

        if ret.parsed is None:
            raise Exception("Failed to create Model Registry connection.", ret.content)

        return ModelRegistry(client=self, data={"id": ret.parsed.id})

    def list_model_registries(self, workspace_id: Optional[int] = None):
        from .wallaroo_ml_ops_api_client.api.model.list_registries import sync
        from .wallaroo_ml_ops_api_client.models.list_registries_request import (
            ListRegistriesRequest,
        )

        workspace_id = (
            workspace_id
            if workspace_id is not None
            else self.get_current_workspace()._id
        )
        ret = sync(
            client=self.mlops(),
            body=ListRegistriesRequest(workspace_id=workspace_id),
        )

        if ret is None:
            raise Exception("Failed to list all Model Registries")

        return ModelRegistriesList([ModelRegistry(self, d.to_dict()) for d in ret])

    def get_email_by_id(self, id: str):
        return User.get_email_by_id(client=self, id=id)

    def remove_edge(
        self,
        name: str,
    ):
        """Remove an edge to a published pipeline.

        :param str name: The name of the edge that will be removed. This is not limited to this pipeline.
        """

        res = removeEdgeSync(
            client=self.mlops(),
            body=RemoveEdgeBody(
                name=name,
                # pipeline_publish_id=self.id,
            ),
        )
        if res.status_code != HTTPStatus.OK:
            raise Exception("Failed to remove edge to published pipeline.", res.content)

    def _get_id_for_workspace(
        self, workspace_id: Optional[int] = None, workspace_name: Optional[str] = None
    ):
        if workspace_name is not None and workspace_id is None:
            try:
                workspace = self.get_workspace(
                    name=workspace_name, create_if_not_exist=False
                )
            except Exception:
                raise Exception(f"Workspace by name {workspace_name} is not found")
            if workspace is not None:
                workspace_id = workspace.id()
        return workspace_id

    @staticmethod
    def _validate_workspace_id(workspace_id: Optional[int]):
        if workspace_id is not None and not isinstance(workspace_id, int):
            raise TypeError("Workspace ID must be an integer.")

    @staticmethod
    def _validate_workspace_name(workspace_name: Optional[str]):
        if workspace_name is not None:
            if not isinstance(workspace_name, str):
                raise TypeError("Workspace name must be a string.")

    @staticmethod
    def _add_filter_and_param_to_query(
        filters: List[str],
        params: Dict[str, Any],
        query_params: List[str],
        filter_db_field: str,
        filter_key: str,
        filter_value: Any,
        filter_type: str,
    ):
        if filter_value is not None:
            filters.append(f"{filter_db_field}: {{_eq: ${filter_key}}}")
            params[filter_key] = filter_value
            query_params.append(f"${filter_key}: {filter_type}!")
        return filters, params, query_params

    def _setup_mlops_client(self) -> "MLOpsClient":
        headers = {
            "user-agent": _user_agent,
        }
        self._mlops = MLOpsClient(
            base_url=self.api_endpoint,
            token=self.auth._access_token().token,
            headers=headers,
        ).with_timeout(httpx.Timeout(60, connect=5.0))
        return self._mlops

    def mlops(self) -> "MLOpsClient":
        return self._setup_mlops_client()
