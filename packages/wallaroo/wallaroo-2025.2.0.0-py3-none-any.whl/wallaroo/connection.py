from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .object import Object, RequiredAttributeMissing, rehydrate, value_if_present

if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    from .client import Client


class Connection(Object):
    """Connection to an external data source or destination."""

    def __init__(self, client: Client, data: Dict[str, Any]) -> None:
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
        self._type = value_if_present(data, "type")
        self._details = value_if_present(data, "details")
        self._created_at = value_if_present(data, "created_at")
        self._workspace_names = value_if_present(data, "workspace_names")

    def _fetch_attributes(self) -> Dict[str, Any]:
        from wallaroo.wallaroo_ml_ops_api_client.api.connection.connections_get_by_id import (
            ConnectionsGetByIdResponse200,
            sync,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models.connections_get_by_id_body import (
            ConnectionsGetByIdBody,
        )

        res = sync(
            client=self.client.mlops(),
            body=ConnectionsGetByIdBody.from_dict({"id": self.id()}),
        )

        if res is None or not isinstance(res, ConnectionsGetByIdResponse200):
            raise Exception("Failed to fetch connection")

        return res.to_dict()

    @staticmethod
    def list_connections(
        client: Client, workspace_id: Optional[int] = None
    ) -> ConnectionList:
        from wallaroo.wallaroo_ml_ops_api_client.api.connection.connections_list import (
            ConnectionsListResponse200,
            sync,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models.connections_list_body import (
            ConnectionsListBody,
        )

        json_body = (
            ConnectionsListBody()
            if workspace_id is None
            else ConnectionsListBody.from_dict({"workspace_id": workspace_id})
        )

        res = sync(
            client=client.mlops(),
            body=json_body,
        )

        if res is None:
            raise Exception("Failed to list connections")

        if not isinstance(res, ConnectionsListResponse200):
            raise Exception(res.msg)

        return ConnectionList(
            [Connection(client=client, data=v.to_dict()) for v in res.connections]
        )

    @staticmethod
    def get_connection(client: Client, name: str) -> Connection:
        from wallaroo.wallaroo_ml_ops_api_client.api.connection.connections_get import (
            ConnectionsGetResponse200,
            sync,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models.connections_get_body import (
            ConnectionsGetBody,
        )

        res = sync(
            client=client.mlops(),
            body=ConnectionsGetBody.from_dict({"name": name}),
        )

        if res is None or not isinstance(res, ConnectionsGetResponse200):
            raise Exception("Failed to get connection")

        return Connection(client=client, data=res.to_dict())

    @staticmethod
    def create_connection(
        client: Client, name: str, connection_type: str, details: Dict[str, Any]
    ) -> Connection:
        from wallaroo.wallaroo_ml_ops_api_client.api.connection.connections_create import (
            ConnectionsCreateResponse200,
            ConnectionsCreateResponse409,
            sync,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models.connections_create_body import (
            ConnectionsCreateBody,
        )

        res = sync(
            client=client.mlops(),
            body=ConnectionsCreateBody.from_dict(
                {
                    "name": name,
                    "type": connection_type,
                    "details": details,
                }
            ),
        )

        if isinstance(res, ConnectionsCreateResponse409):
            raise Exception(
                "This connection already exists.  Please choose a different connection name."
            )

        if not isinstance(res, ConnectionsCreateResponse200):
            raise Exception("Failed to create connection")

        return Connection(client=client, data=res.to_dict())

    def delete_connection(self):
        from wallaroo.wallaroo_ml_ops_api_client.api.connection.connections_delete import (
            sync,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models.connections_delete_body import (
            ConnectionsDeleteBody,
        )

        _ = sync(
            client=self.client.mlops(),
            body=ConnectionsDeleteBody.from_dict({"name": self.name()}),
        )

    def add_connection_to_workspace(self, workspace_id: int):
        from wallaroo.wallaroo_ml_ops_api_client.api.connection.connections_add_to_workspace import (
            sync,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models.connections_add_to_workspace_body import (
            ConnectionsAddToWorkspaceBody,
        )

        res = sync(
            client=self.client.mlops(),
            body=ConnectionsAddToWorkspaceBody.from_dict(
                {"connection_id": self.id(), "workspace_id": workspace_id}
            ),
        )

        if res is None:
            raise Exception("Failed to add connection to workspace")

    def remove_connection_from_workspace(self, workspace_id: int):
        from wallaroo.wallaroo_ml_ops_api_client.api.connection.connections_remove_from_workspace import (
            sync,
        )
        from wallaroo.wallaroo_ml_ops_api_client.models.connections_remove_from_workspace_body import (
            ConnectionsRemoveFromWorkspaceBody,
        )

        _ = sync(
            client=self.client.mlops(),
            body=ConnectionsRemoveFromWorkspaceBody.from_dict(
                {"connection_id": self.id(), "workspace_id": workspace_id}
            ),
        )

    def id(self):
        return self._id

    @rehydrate("_name")
    def name(self):
        return self._name

    @rehydrate("_type")
    def connection_type(self):
        return self._type

    @rehydrate("_details")
    def details(self):
        return self._details

    @rehydrate("_created_at")
    def created_at(self):
        return self._created_at

    @rehydrate("_workspace_names")
    def workspace_names(self):
        return self._workspace_names

    def _repr_html_(self) -> str:
        return f"""
        <table>
          <tr>
            <th>Field</th>
            <th>Value</th>
          </tr>
          <tr>
            <td>Name</td><td>{self.name()}</td>
          </tr>
          <tr>
            <td>Connection Type</td><td>{self.connection_type()}</td>
          </tr>
          <tr>
            <td>Details</td><td>*****</td>
          </tr>
          <tr>
            <td>Created At</td><td>{self.created_at()}</td>
          </tr>
          <tr>
            <td>Linked Workspaces</td><td>{self.workspace_names()}</td>
          </tr>
        </table>
        """


class ConnectionList(List[Connection]):
    """Wraps a list of connections for display in a display-aware environment like Jupyter."""

    def _repr_html_(self) -> str:
        def row(connection):
            return (
                "<tr>"
                + f"<td>{connection.name()}</td>"
                + f"<td>{connection.connection_type()}</td>"
                + "<td>*****</td>"
                + f"<td>{connection.created_at()}</td>"
                + f"<td>{connection.workspace_names()}</td>"
                + "</tr>"
            )

        fields = [
            "name",
            "connection type",
            "details",
            "created at",
            "linked workspaces",
        ]

        if self == []:
            return "(no connections)"
        else:
            return (
                "<table>"
                + "<tr><th>"
                + "</th><th>".join(fields)
                + "</th></tr>"
                + ("".join([row(p) for p in self]))
                + "</table>"
            )
