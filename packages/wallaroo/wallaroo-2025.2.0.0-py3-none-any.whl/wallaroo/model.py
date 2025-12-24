import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

from dateutil import parser as dateparse

from wallaroo.utils import _unwrap

from .model_version import ModelVersion
from .object import (
    DehydratedValue,
    Object,
    RequiredAttributeMissing,
    rehydrate,
    value_if_present,
)
from .wallaroo_ml_ops_api_client.api.model import models_get
from .wallaroo_ml_ops_api_client.models import models_get_body
from .wallaroo_ml_ops_api_client.models.models_get_response_500 import (
    ModelsGetResponse500,
)

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client
    from .model_config import ModelConfig
    from .model_version import ModelVersion
    from .workspace import Workspace


# wraps the backend models object
class Model(Object):
    """
    A Wallaroo Model object. Each Model may have multiple model versions, accessed via .versions()
    """

    def __init__(self, client: "Client", data: Dict[str, Any]) -> None:
        self.client = client
        self._config: Optional["ModelConfig"] = None
        super().__init__(
            gql_client=client._gql_client if client is not None else None,
            data=data,
        )

    def __repr__(self) -> str:
        return str(
            {
                "name": self.name(),
                "versions": len(self.versions()),
                "owner_id": self.owner_id(),
                "last_update_time": self.last_update_time(),
                "created_at": self.created_at(),
            }
        )

    def _repr_html_(self) -> str:
        return f"""
          <table>
            <tr>
              <th>Name</td>
              <td>{self.name()}</td>
            </tr>
            <tr>
              <th># of Versions</td>
              <td>{len(self.versions())}</td>
            </tr>
            <tr>
              <th>Owner ID</td>
              <td>{self.owner_id()}</td>
            </tr>
            <tr>
              <th>Last Updated</td>
              <td>{self.last_update_time()}</td>
            </tr>
            <tr>
              <th>Created At</td>
              <td>{self.created_at()}</td>
            </tr>
            <tr>
                <th>Workspace id</td>
                <td>{self.workspace().id()}</td>
            </tr>
            <tr>
                <th>Workspace name</td>
                <td>{self.workspace().name()}</td>
            </tr>
          </table>
        """

    def _fill(self, data: Dict[str, Any]) -> None:
        """Fills an object given a response dictionary from the GraphQL API.

        Only the primary key member must be present; other members will be
        filled in via rehydration if their corresponding member function is
        called.
        """
        from .workspace import Workspace

        for required_attribute in ["id"]:
            if required_attribute not in data:
                raise RequiredAttributeMissing(
                    self.__class__.__name__, required_attribute
                )
        # Required
        self._id = data["id"]

        # Optional
        self._name = value_if_present(data, "name")
        self._owner_id = value_if_present(data, "owner_id")
        self._created_at = (
            dateparse.isoparse(data["created_at"])
            if "created_at" in data
            else DehydratedValue()
        )
        self._last_update_time = (
            dateparse.isoparse(data["updated_at"])
            if "updated_at" in data
            else DehydratedValue()
        )

        self._versions = (
            [ModelVersion(client=self.client, data=x) for x in data["models"]]
            if "models" in data
            else DehydratedValue()
        )
        self._workspace = (
            Workspace(self.client, data["workspace"])
            if "workspace" in data
            else DehydratedValue()
        )

    def _fetch_attributes(self) -> Dict[str, Any]:
        """Fetches all member data from the GraphQL API."""
        client = _unwrap(self.client)
        ret = models_get.sync(
            client=client.mlops(),
            body=models_get_body.ModelsGetBody(self.id()),
        )

        if isinstance(ret, ModelsGetResponse500):
            raise RuntimeError(ret.msg)

        if ret is None:
            raise RuntimeError("An error occurred loading the model.")

        return ret.to_dict()

    def id(self) -> int:
        return self._id

    @rehydrate("_name")
    def name(self) -> str:
        return cast(str, self._name)

    @rehydrate("_owner_id")
    def owner_id(self) -> str:
        return cast(str, self._owner_id)

    @rehydrate("_last_update_time")
    def last_update_time(self) -> datetime.datetime:
        return cast(datetime.datetime, self._last_update_time)

    @rehydrate("_created_at")
    def created_at(self) -> datetime.datetime:
        return cast(datetime.datetime, self._created_at)

    @rehydrate("_versions")
    def versions(self) -> List["ModelVersion"]:
        return cast(List["ModelVersion"], self._versions)

    @rehydrate("_workspace")
    def workspace(self) -> "Workspace":
        from .workspace import Workspace

        return cast(Workspace, self._workspace)


class ModelList(List[Model]):
    """Wraps a list of Models for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(model: Model):
            return f"""
            <tr>
              <td>{model.name()}</td>
              <td>{len(model.versions())}</td>
              <td>{model.owner_id()}</td>
              <td>{model.last_update_time()}</td>
              <td>{model.created_at()}</td>
              <td>{model.workspace().id()}</td>
              <td>{model.workspace().name()}</td>
            </tr>
          """

        fields = [
            "Name",
            "# of Versions",
            "Owner ID",
            "Last Updated",
            "Created At",
            "Workspace id",
            "Workspace name",
        ]

        if self == []:
            return "(no models)"
        else:
            return (
                "<table>"
                + "<tr>"
                + "".join([f"<th>{field}</th>" for field in fields])
                + "</tr>"
                + "".join([row(models) for models in self])
                + "</table>"
            )
