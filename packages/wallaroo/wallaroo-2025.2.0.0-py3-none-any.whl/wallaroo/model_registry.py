from __future__ import annotations

import base64
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List

import pyarrow as pa  # type: ignore
from dateutil import parser as dateparse

from wallaroo.framework import Framework
from wallaroo.model_version import ModelVersion
from wallaroo.wallaroo_ml_ops_api_client.models import registered_model_version

from .object import (
    DehydratedValue,
    Object,
    RequiredAttributeMissing,
    rehydrate,
    value_if_present,
)
from .wallaroo_ml_ops_api_client.models.dbfs_list_response_file_with_full_path import (
    DbfsListResponseFileWithFullPath,
)
from .wallaroo_ml_ops_api_client.models.registered_model import (
    RegisteredModel as APIRegisteredModel,
)

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client


class ModelRegistry(Object):
    """
    An instance of an external Model Registry.
    Currently, the supported registries are: DataBricks
    """

    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
        self.client = client

        super().__init__(
            gql_client=client._gql_client,
            data=data,
        )

    def _fill(self, data: Dict[str, Any]) -> None:
        for required_attribute in ["id"]:
            if required_attribute not in data:
                raise RequiredAttributeMissing(
                    self.__class__.__name__, required_attribute
                )
        # Required
        self._id = data["id"]
        # Optional
        self._name = value_if_present(data, "name")
        self._url = value_if_present(data, "url")
        self._token = value_if_present(data, "token")
        self._workspaces = value_if_present(data, "workspaces")

        self._created_at: datetime | DehydratedValue = (
            dateparse.isoparse(data["created_at"])
            if "created_at" in data
            else DehydratedValue()
        )

        self._updated_at: datetime | DehydratedValue = (
            dateparse.isoparse(data["updated_at"])
            if "updated_at" in data
            else DehydratedValue()
        )

    def _fetch_attributes(self) -> Dict[str, Any]:
        from .wallaroo_ml_ops_api_client.api.model.get_registry import sync
        from .wallaroo_ml_ops_api_client.models.get_registry_request import (
            GetRegistryRequest,
        )

        ret = sync(client=self.client.mlops(), body=GetRegistryRequest(self._id))

        if ret is None:
            raise Exception("Failed to find a registry with id: " + self._id)

        return ret.to_dict()

    @rehydrate("_name")
    def name(self):
        return self._name

    @rehydrate("_id")
    def id(self):
        return self._id

    @rehydrate("_url")
    def url(self):
        return self._url

    @rehydrate("_created_at")
    def created_at(self):
        return self._created_at

    @rehydrate("_updated_at")
    def updated_at(self):
        return self._updated_at

    @rehydrate("_workspaces")
    def workspaces(self):
        return self._workspaces

    def add_registry_to_workspace(self, workspace_id: int):
        from .wallaroo_ml_ops_api_client.api.model.attach_registry_to_workspace import (
            sync,
        )
        from .wallaroo_ml_ops_api_client.models.attach_registry_to_workspace_request import (
            AttachRegistryToWorkspaceRequest,
        )

        ret = sync(
            client=self.client.mlops(),
            body=AttachRegistryToWorkspaceRequest(self._id, workspace_id),
        )

        if ret is None:
            raise Exception("Failed to attach registry to workspace")

        return self

    def remove_registry_from_workspace(self, workspace_id: int):
        from .wallaroo_ml_ops_api_client.api.model.remove_registry_from_workspace import (
            sync,
        )
        from .wallaroo_ml_ops_api_client.models.remove_registry_from_workspace_request import (
            RemoveRegistryFromWorkspaceRequest,
        )

        ret = sync(
            client=self.client.mlops(),
            body=RemoveRegistryFromWorkspaceRequest(self._id, workspace_id),
        )

        if ret is None:
            raise Exception("Failed to remove registry from workspace.")

        return self

    def list_models(self):
        from .wallaroo_ml_ops_api_client.api.model.list_registry_models import sync
        from .wallaroo_ml_ops_api_client.models.list_registry_models_request import (
            ListRegistryModelsRequest,
        )

        ret = sync(client=self.client.mlops(), body=ListRegistryModelsRequest(self._id))

        if ret is None:
            return []

        return RegisteredModels(
            [
                RegisteredModel(client=self.client, data=m, registry_id=self._id)
                for m in ret.registered_models
            ]
        )

    def upload_model(
        self,
        name: str,
        path: str,
        framework: Framework,
        input_schema: pa.Schema,
        output_schema: pa.Schema,
        requirements: List[str] = [],
    ) -> ModelVersion:
        """
        :param: name str A descriptive name to set
        :param: path str The DBFS path to the artifact file to upload.
        :param: framework Framework The ML framework that this model uses (ex. Framework.ONNX).
        :param: requirements List[str] An optional list of python requirements needed to run this model.
        :param: input_schema pa.Schema A PyArrow schema describing inputs to this model.
        :param: output_schema pa.Schema A PyArrow schema describing the outputs of this model.
        :return: Model An instance of the Wallaroo model that is being created.
        """
        from .wallaroo_ml_ops_api_client.api.model.upload_from_registry import (
            sync,
        )
        from .wallaroo_ml_ops_api_client.models import UploadFromRegistryBody
        from .wallaroo_ml_ops_api_client.models.conversion import Conversion

        i_s = base64.b64encode(bytes(input_schema.serialize())).decode("utf8")
        o_s = base64.b64encode(bytes(output_schema.serialize())).decode("utf8")

        ret = sync(
            client=self.client.mlops(),
            body=UploadFromRegistryBody(
                path=path,
                name=name,
                registry_id=self._id,
                conversion=Conversion(
                    framework=framework._to_openapi_framework(),
                    requirements=requirements,
                ),
                input_schema=i_s,
                output_schema=o_s,
                visibility="private",
                workspace_id=self.client.get_current_workspace()._id,
            ),
        )

        if ret is None:
            raise Exception("Failed to start upload.")

        return ModelVersion(client=self.client, data={"id": ret.model_id})

    def _repr_html_(self):
        self._rehydrate()
        fmt = self.client._time_format
        workspace_list = ", ".join([w.get("name") for w in self._workspaces])
        return f"""<table>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
          <tr>
            <td>Name</td><td>{self._name}</td>
          </tr>
          <tr>
            <td>URL</td><td>{self._url}</td>
          </tr>
          <tr>
            <td>Workspaces</td><td>{workspace_list}</td>
          </tr>
          <tr>
              <td>Created At</td><td>{self._created_at.strftime(fmt)}</td>
          </tr>
          <tr>
              <td>Updated At</td><td>{self._updated_at.strftime(fmt)}</td>
          </tr>
        </table>"""


class ModelRegistriesList(List[ModelRegistry]):
    """Wraps a list of Model Registries for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(registry):
            fmt = registry.client._time_format

            created_at = (
                registry._created_at
                if isinstance(registry._created_at, DehydratedValue)
                else registry._created_at.strftime(fmt)
            )

            updated_at = (
                registry._updated_at
                if isinstance(registry._updated_at, DehydratedValue)
                else registry._updated_at.strftime(fmt)
            )
            return (
                "<tr>"
                + f"<td>{registry._name}</td>"
                + f"<td>{registry._url}</td>"
                + f"<td>{created_at}</td>"
                + f"<td>{updated_at}</td>"
                # + f"<td>{registry.workspace_names()}</td>"
                + "</tr>"
            )

        fields = [
            "name",
            "registry url",
            "created at",
            "updated at",
            # "linked workspaces",
        ]

        if self == []:
            return "(no registrys)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )


class RegisteredModelVersion(registered_model_version.RegisteredModelVersion):
    def __init__(
        self,
        client: Client,
        data: registered_model_version.RegisteredModelVersion,
        registry_id: str,
    ):
        super().__init__(**data.to_dict())
        self._client = client
        self.registry_id = registry_id
        self.created_at = datetime.fromtimestamp(data.creation_timestamp / 1000)
        self.updated_at = datetime.fromtimestamp(data.last_updated_timestamp / 1000)

    # Deprecated code.
    """
    def upload(self, framework: Framework, requirements: List[str] = []):
        # Uploads this Model's source code to your Wallaroo instance.

        #:param: framework Framework The ML framework that this model uses (ex. Framework.ONNX).
        #:param: requirements List[str] An optional list of python requirements needed to run this model.
        #:return: Model An instance of the Wallaroo model that is being created.
        #
        from .wallaroo_ml_ops_api_client.api.model.upload_from_registry import sync
        from .wallaroo_ml_ops_api_client.models.upload_from_registry_request import (
            UploadFromRegistryRequest,
        )
        from .wallaroo_ml_ops_api_client.models.conversion import Conversion

        ret = sync(
            client=self._client.mlops(),
            body=UploadFromRegistryRequest(
                Conversion(
                    framework=framework._to_openapi_framework(),
                    requirements=requirements,
                ),
                self.name,
                self.registry_id,
                self.version,
                "private",
                self._client.get_current_workspace()._id,
            ),
        )

        if ret is None:
            raise Exception("Failed to start upload.")

        return Model(client=self._client, data={"id": ret.model_id})
      """

    def list_artifacts(self):
        from .wallaroo_ml_ops_api_client.api.model.list_registry_model_version_artifacts import (
            sync_detailed,
        )
        from .wallaroo_ml_ops_api_client.models.list_registry_model_version_artifacts_request import (
            ListRegistryModelVersionArtifactsRequest,
        )

        ret = sync_detailed(
            client=self._client.mlops(),
            body=ListRegistryModelVersionArtifactsRequest(
                self.name, self.registry_id, self.version
            ),
        )

        if ret.parsed is None:
            raise Exception(
                f"Failed to list artifacts from remote registry: {ret.content}"
            )

        return DbfsFileList(ret.parsed)

    def _repr_html_(self):
        return f"""
          <table>
            <tr>
              <td>Name</td><td>{self.name}</td>
            </tr>
            <tr>
              <td>Version</td><td>{self.version}</td>
            </tr>
            <tr>
              <td>User</td><td>{self.user_id}</td>
            </tr>
            <tr>
              <td>Description</td><td>{self.description}</td>
            </tr>
            <tr>
              <td>Run ID</td><td>{self.run_id}</td>
            </tr>
            <tr>
              <td>Run Link</td><td>{self.run_link}</td>
            </tr>
            <tr>
              <td>Registry Source</td><td>{self.source}</td>
            </tr>
            <tr>
              <td>Registry Status</td><td>{self.status}</td>
            </tr>
            <tr>
              <td>Created At</td><td>{self.created_at}</td>
            </tr>
            <tr>
              <td>Updated At</td><td>{self.updated_at}</td>
            </tr>
          </table>
        """


class DbfsFileList(List[DbfsListResponseFileWithFullPath]):
    def _repr_html_(self):
        def row(file: DbfsListResponseFileWithFullPath):
            [_, file_name] = file.path.rsplit("/", 1)

            return f"""
            <tr>
              <td>{file_name}</td>
              <td>{file.file_size}B</td>
              <td>{file.full_path}</td>
            </tr>
            """

        return f"""
          <table>
            <tr>
              <th>File Name</th>
              <th>File Size</th>
              <th>Full Path</th>
            </tr>
            {"".join(row(file) for file in self)}
          </table>
        """


class RegisteredModelVersionsList(List[RegisteredModelVersion]):
    """Wraps a list of Model Registries for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(vers: RegisteredModelVersion):
            return f"""
            <tr>
              <td>{vers.name}</td>
              <td>{vers.version}</td>
              <td>{vers.description}</td>
              <td>{vers.user_id}</td>
              <td>{vers.created_at}</td>
              <td>{vers.updated_at}</td>
            </tr>
            """

        return f"""
          <table>
            <tr>
              <td>Name</td>
              <td>Version</td>
              <td>Description</td>
              <td>User</td>
              <td>Created At</td>
              <td>Updated At</td>
            </tr>
            {"".join([row(vers) for vers in self])}
          </table>
        """


class RegisteredModel:
    """This is a reference to a Registered Model in an external registry."""

    def __init__(
        self,
        client: Client,
        data: APIRegisteredModel,
        registry_id: str,
    ):
        from .wallaroo_ml_ops_api_client.types import Unset

        self._client = client
        self.created_at = datetime.fromtimestamp(data.creation_timestamp / 1000)
        self.updated_at = datetime.fromtimestamp(data.last_updated_timestamp / 1000)
        self.name = data.name
        self.registry_user = data.user_id
        self.registry_id = registry_id
        latest_versions = (
            data.latest_versions
            if data.latest_versions is not None
            and not isinstance(data.latest_versions, Unset)
            else []
        )
        self.latest_versions = RegisteredModelVersionsList(
            [
                RegisteredModelVersion(client, vers, registry_id=self.registry_id)
                for vers in latest_versions
            ]
        )

    def versions(self):
        from .wallaroo_ml_ops_api_client.api.model.list_registry_model_versions import (
            sync_detailed,
        )
        from .wallaroo_ml_ops_api_client.models.list_registry_model_versions_request import (
            ListRegistryModelVersionsRequest,
        )

        ret = sync_detailed(
            client=self._client.mlops(),
            body=ListRegistryModelVersionsRequest(self.name, self.registry_id),
        )

        if ret.status_code != 200:
            print(ret)
            raise Exception("Failed to pull versions from MLFlow registry")

        return RegisteredModelVersionsList(
            [
                RegisteredModelVersion(
                    client=self._client, data=x, registry_id=self.registry_id
                )
                for x in ret.parsed.model_versions
            ]
        )

    def list_artifacts(self):
        recent_version = self.versions[0]
        print(
            f"Listing artifacts for the most recent version ({recent_version.version})"
        )
        return recent_version.list_artifacts()

    def _repr_html_(self):
        fmt = self._client._time_format
        return f"""
        <table>
          <tr>
            <td>Name</td>
            <td>{self.name}</td>
          </tr>
          <tr>
            <td>Registry User</td>
            <td>{self.registry_user}</td>
          </tr>
          <tr>
            <td>Versions</td>
            <td>{len(self.versions())}</td>
          </tr>
          <tr>
            <td>Created At</td>
            <td>{self.created_at.strftime(fmt)}</td>
          </tr>
          <tr>
            <td>Updated At</td>
            <td>{self.updated_at.strftime(fmt)}</td>
          </tr>
        </table>
        """


class RegisteredModels(List[RegisteredModel]):
    """This is a list of Registered Models in an external registry."""

    def _repr_html_(self):
        def row(model: RegisteredModel):
            fmt = model._client._time_format

            return f"""
              <tr>
                <td>{model.name}</td>
                <td>{model.registry_user}</td>
                <td>{model.created_at.strftime(fmt)}</td>
                <td>{model.updated_at.strftime(fmt)}</td>
              </tr>
            """

        return f"""
        <table>
          <tr>
            <td>Name</td>
            <td>Registry User</td>
            <td>Created At</td>
            <td>Updated At</td>
          </tr>
          {"".join([row(x) for x in self])}
        </table>
        """
