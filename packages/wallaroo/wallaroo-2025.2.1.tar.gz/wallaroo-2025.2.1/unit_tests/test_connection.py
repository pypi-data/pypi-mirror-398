import datetime

import httpx
import respx

import wallaroo
from wallaroo.connection import Connection
from wallaroo.workspace import *

from . import testutil


class TestConnection:
    def setup_method(self):
        self.ix = 0
        self.now = datetime.datetime.now()
        self.gql_client = testutil.new_gql_client(
            endpoint="http://api-lb:8080/v1/graphql",
        )
        self.test_client = wallaroo.Client(
            gql_client=self.gql_client,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )

    def add_get_connection_responder(self, respx_mock):
        get_connection_resp = {
            "id": "99cace15-e0d4-4bb6-bf14-35efee181b90",
            "name": "test-connection",
            "type": "ODBC",
            "details": {
                "key1": "value1",
                "key2": "value2",
            },
            "created_at": "2022-03-02T08:13:38.627443",
            "workspace_names": [],
        }
        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/connections/get").mock(
            return_value=httpx.Response(200, json=get_connection_resp)
        )

    @respx.mock(assert_all_mocked=True)
    def test_list_connections(self, respx_mock):
        list_connections_resp = {
            "connections": [
                {
                    "id": "99cace15-e0d4-4bb6-bf14-35efee181b90",
                    "name": "test-connection",
                    "type": "ODBC",
                    "details": {
                        "key1": "value1",
                        "key2": "value2",
                    },
                    "created_at": "2022-03-02T08:13:38.627443",
                    "workspace_names": [],
                }
            ]
        }
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/connections/list"
        ).mock(return_value=httpx.Response(200, json=list_connections_resp))

        cons = self.test_client.list_connections()
        assert len(cons) > 0
        assert isinstance(cons[0], Connection)
        assert cons[0].id() == "99cace15-e0d4-4bb6-bf14-35efee181b90"

    @respx.mock(assert_all_mocked=True)
    def test_create_connection(self, respx_mock):
        get_connection_resp = {
            "id": "99cace15-e0d4-4bb6-bf14-35efee181b90",
            "name": "test-connection",
            "type": "ODBC",
            "details": {
                "key1": "value1",
                "key2": "value2",
            },
            "created_at": "2022-03-02T08:13:38.627443",
            "workspace_names": [],
        }
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/connections/create"
        ).mock(return_value=httpx.Response(200, json=get_connection_resp))

        conn = self.test_client.create_connection(
            name="test-connection",
            connection_type="ODBC",
            details={
                "key1": "value1",
                "key2": "value2",
            },
        )
        assert isinstance(conn, Connection)
        assert conn.id() == "99cace15-e0d4-4bb6-bf14-35efee181b90"

    @respx.mock(assert_all_mocked=True)
    def test_delete_connection(self, respx_mock):
        conn = Connection(
            self.test_client,
            data={
                "id": "99cace15-e0d4-4bb6-bf14-35efee181b90",
                "name": "test-connection",
            },
        )
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/connections/delete"
        ).mock(return_value=httpx.Response(204))

        conn.delete_connection()

    @respx.mock(assert_all_mocked=True)
    def test_add_workspace_connection(self, respx_mock):
        self.add_get_connection_responder(respx_mock)
        add_connection_resp = {
            "id": "ok",
        }
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/connections/add_to_workspace"
        ).mock(return_value=httpx.Response(200, json=add_connection_resp))

        ws = Workspace(client=self.test_client, data={"id": 1})
        ws.add_connection(name="test")

    @respx.mock(assert_all_mocked=True)
    def test_remove_workspace_connection(self, respx_mock):
        self.add_get_connection_responder(respx_mock)
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/connections/remove_from_workspace"
        ).mock(return_value=httpx.Response(200))

        ws = Workspace(client=self.test_client, data={"id": 1})
        ws.remove_connection(name="test")
