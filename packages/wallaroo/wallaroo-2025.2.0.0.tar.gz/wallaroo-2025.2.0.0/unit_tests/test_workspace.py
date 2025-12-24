import datetime

import httpx
import pytest
import respx

import wallaroo
from wallaroo.workspace import Workspace

from . import testutil
from .reusable_responders import add_get_workspace_by_id_responder


class TestWorkspace:
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

    def add_user_responder(self, respx_mock):
        respx_mock.get(
            "http://mock-keycloak:1234/auth/admin/realms/master/users",
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "99cace15-e0d4-4bb6-bf14-35efee181b90",
                        "createdTimestamp": 1645626193993,
                        "username": "ci",
                        "enabled": True,
                        "totp": False,
                        "emailVerified": True,
                        "email": "x@c.co",
                        "disableableCredentialTypes": [],
                        "requiredActions": [],
                        "notBefore": 0,
                        "access": {
                            "manageGroupMembership": True,
                            "view": True,
                            "mapRoles": True,
                            "impersonate": True,
                            "manage": True,
                        },
                    },
                ],
            ),
        )

    def add_workspace_user_create_responder(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/workspaces/add_user",
        ).mock(
            return_value=httpx.Response(
                200,
                json={},
            ),
        )

    def add_user_by_id_responder(
        self, respx_mock, auth_url="http://mock-keycloak:1234", n=1
    ):
        respx_mock.get(f"{auth_url}/auth/admin/realms/master/users/{n}").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "99cace15-e0d4-4bb6-bf14-35efee181b90",
                    "createdTimestamp": 1645626193993,
                    "username": "ci",
                    "enabled": True,
                    "totp": False,
                    "emailVerified": True,
                    "email": "x@c.co",
                    "disableableCredentialTypes": [],
                    "requiredActions": [],
                    "notBefore": 0,
                    "access": {
                        "manageGroupMembership": True,
                        "view": True,
                        "mapRoles": True,
                        "impersonate": True,
                        "manage": True,
                    },
                },
            )
        )

    def add_create_workspace_responder(self, respx_mock, expected_id=1):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/workspaces/create"
        ).mock(return_value=httpx.Response(200, json={"workspace_id": expected_id}))

    def add_list_workspace_responder(self, respx_mock):
        list_workspace_resp = {
            "workspaces": [
                {
                    "id": 1,
                    "name": "test-workspace",
                    "created_at": "2022-03-02T08:13:38.627443",
                    "created_by": "44",
                    "pipelines": [],
                    "models": {"models": []},
                    "users": [],
                    "archived": False,
                }
            ]
        }
        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/workspaces/list").mock(
            return_value=httpx.Response(200, json=list_workspace_resp)
        )

    def add_list_workspace_responder_with_no_workspaces(self, respx_mock):
        list_workspace_resp = {"workspaces": []}
        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/workspaces/list").mock(
            return_value=httpx.Response(200, json=list_workspace_resp)
        )

    def teardown_module(self):
        pass

    def test_init_full_dict(self):
        ws = Workspace(
            client=self.test_client,
            data={
                "id": 1,
                "name": "myws",
                "archived": False,
                "models": [{"id": 1}, {"id": 2}],
                "pipelines": [{"id": 1}],
                "created_at": self.now.isoformat(),
                "created_by": 42,
                "users": [{"id": 7}, {"id": 8}],
            },
        )

        assert 1 == ws.id()
        assert "myws" == ws.name()
        assert 2 == len(ws._models)
        assert 1 == len(ws._pipelines)
        assert ws._models[0]["id"] == 1
        assert ws._models[1]["id"] == 2
        assert ws._pipelines[0]["id"] == 1
        assert str(self.now.isoformat()) == ws.created_at()

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_rehydrate(self, respx_mock):
        testcases = [
            ("name", "test-workspace"),
            ("created_at", self.now.isoformat()),
            ("created_by", 44),
            ("models", []),
            ("pipelines", []),
            ("archived", False),
        ]
        for method_name, want_value in testcases:
            respx_mock.post(
                "http://api-lb:8080/v1/graphql",
                content__contains="query WorkspaceById",
            ).mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "data": {
                            "workspace_by_pk": {
                                "id": 1,
                                "name": "test-workspace",
                                "created_at": self.now.isoformat(),
                                "created_by": 44,
                                "pipelines": [],
                                "models": [],
                                "users": [],
                                "archived": False,
                            }
                        },
                    },
                ),
            )

            ws = Workspace(client=self.test_client, data={"id": 1})
            got_value = getattr(ws, method_name)()

            if want_value is not None:
                assert want_value == got_value
            if method_name == "models" or method_name == "pipelines":
                assert 2 == len(respx_mock.calls)
            else:
                assert 1 == len(respx_mock.calls)

            # Another call to the same accessor shouldn't trigger any
            # additional GraphQL queries.
            got_value = getattr(ws, method_name)()
            if want_value is not None:
                assert want_value == got_value

            if method_name == "models" or method_name == "pipelines":
                assert 3 == len(respx_mock.calls)
            else:
                assert 1 == len(respx_mock.calls)
            respx_mock.reset()

    @respx.mock(assert_all_mocked=True)
    def test_get_user_default_workspace(self, respx_mock):
        client = self.test_client
        respx_mock.post(
            "http://api-lb:8080/v1/graphql",
            content__contains="query UserDefaultWorkspace",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "user_default_workspace": [
                            {
                                "workspace": {
                                    "archived": False,
                                    "created_at": "2022-02-15T09:42:12.857637+00:00",
                                    "created_by": "bb2dec32-09a1-40fd-8b34-18bd61c9c070",
                                    "name": "345fr",
                                    "id": 1,
                                    "pipelines": [],
                                    "models": [],
                                }
                            }
                        ]
                    }
                },
            ),
        )

        ws = Workspace._get_user_default_workspace(client)
        assert isinstance(ws, Workspace)
        assert ws.id() == 1
        assert ws.archived() == False
        assert ws.name() == "345fr"
        assert ws._pipelines == []
        assert ws._models == []

    @respx.mock(assert_all_mocked=True)
    def test_create_user_default_workspace(self, respx_mock):
        client = self.test_client
        respx_mock.post(
            "http://api-lb:8080/v1/graphql",
            content__contains="mutation CreateDefaultUserWorkspace",
        ).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"insert_workspace_one": {"id": 5}}},
            ),
        )
        ws = Workspace._create_user_default_workspace(client)
        assert ws._id == 5

    @respx.mock(assert_all_mocked=True)
    def test_create_workspace(self, respx_mock):
        client = self.test_client

        self.add_create_workspace_responder(respx_mock, expected_id=11)

        ws = Workspace._create_workspace(client, name="foo")
        assert isinstance(ws, Workspace)
        assert ws.id() == 11

    @respx.mock(assert_all_mocked=True)
    def test_list_workspaces(self, respx_mock):
        self.add_list_workspace_responder(respx_mock)
        wss = self.test_client.list_workspaces()
        assert len(wss) > 0
        assert isinstance(wss[0], Workspace)
        assert wss[0].id() == 1

    @respx.mock(assert_all_mocked=True)
    def test_list_workspaces_html(self, respx_mock):
        self.add_list_workspace_responder(respx_mock)

        respx_mock.post(
            "http://api-lb:8080/v1/graphql",
            content__contains="query WorkspaceById",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "workspace_by_pk": {
                            "id": 1,
                            "name": "test-workspace",
                            "created_at": "2022-03-02T08:13:38.627443",
                            "created_by": 44,
                            "pipelines": [],
                            "models": [],
                            "users": [],
                            "archived": False,
                        }
                    },
                },
            ),
        )

        wstr = self.test_client.list_workspaces()._repr_html_()
        assert isinstance(wstr, str)
        assert "<table>" in wstr
        assert "<td>2022-03-02 08:13:38</td>" in wstr

    def test_get_set_current_workspace(self):
        client = self.test_client
        ws = Workspace(
            client=client,
            data={
                "id": 1,
            },
        )

        res1 = client.set_current_workspace(ws)
        assert isinstance(res1, Workspace)
        assert ws == res1

        res2 = client.get_current_workspace()
        assert ws == res2

    @respx.mock(assert_all_mocked=True)
    def test_users(self, respx_mock):
        self.add_user_by_id_responder(
            respx_mock, auth_url=self.test_client.api_endpoint, n="UUID-3"
        )
        self.add_user_by_id_responder(
            respx_mock, auth_url=self.test_client.api_endpoint, n="UUID-4"
        )
        respx_mock.post(
            self.test_client.api_endpoint + "/v1/graphql",
            content__contains="query WorkspaceById",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "workspace_by_pk": {
                            "id": 1,
                            "name": "test-workspace",
                            "created_at": self.now.isoformat(),
                            "created_by": 44,
                            "pipelines": [],
                            "models": [],
                            "users": [{"user_id": "UUID-3"}, {"user_id": "UUID-4"}],
                            "archived": False,
                        }
                    },
                },
            ),
        )

        ws = Workspace(client=self.test_client, data={"id": 1})
        users = ws.users()
        assert len(users) == 2
        assert users[0].id() == "99cace15-e0d4-4bb6-bf14-35efee181b90"

    @respx.mock(assert_all_mocked=True)
    def test_add_user(self, respx_mock):
        owner_email = "jane@ex.co"
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/workspaces/add_user"
        ).mock(return_value=httpx.Response(200))
        respx_mock.get(
            f"{self.test_client.api_endpoint}/auth/admin/realms/master/users?email=jane%40ex.co"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "1",
                        "email": owner_email,
                        "username": "jane",
                        "enabled": True,
                        "createdTimestamp": 1645626193993,
                    }
                ],
            )
        )
        ws = Workspace(
            client=self.test_client,
            data={
                "id": 1,
            },
        )

        newws = ws.add_owner(owner_email)
        assert isinstance(newws, Workspace)
        assert newws._id == 1

    @respx.mock(assert_all_mocked=True)
    def test_add_owner(self, respx_mock):
        owner_email = "jane@ex.co"
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/workspaces/add_user"
        ).mock(return_value=httpx.Response(200))

        respx_mock.get(
            f"{self.test_client.api_endpoint}/auth/admin/realms/master/users?email=jane%40ex.co"
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "1",
                        "email": owner_email,
                        "username": "jane",
                        "enabled": True,
                        "createdTimestamp": 1645626193993,
                    }
                ],
            )
        )
        ws = Workspace(
            client=self.test_client,
            data={
                "id": 1,
            },
        )

        newws = ws.add_owner(owner_email)
        assert isinstance(newws, Workspace)
        assert newws._id == 1

    @respx.mock(assert_all_mocked=True)
    def test_models(self, respx_mock):
        """
        Test that Workspaces count the appropriate number of models returned from the query.
        """
        respx_mock.post(
            "http://api-lb:8080/v1/graphql",
            content__contains="query WorkspaceById",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "workspace_by_pk": {
                            "id": 1,
                            "name": "test-workspace",
                            "created_at": self.now.isoformat(),
                            "created_by": 44,
                            "pipelines": [],
                            "models": [{"id": 1}, {"id": 2}],
                            "users": [{"user_id": "UUID-3"}, {"user_id": "UUID-4"}],
                            "archived": False,
                        }
                    },
                },
            ),
        )

        ws = Workspace(client=self.test_client, data={"id": 1})
        models = ws.models()
        assert len(models) == 2

        example_models_1 = {
            "id": 1,
            "created_at": "2022-10-26T14:12:41.040083+00:00",
            "name": "kerasccfraud",
            "owner_id": '""',
            "updated_at": "2022-10-26T14:12:41.040083+00:00",
            "models": [
                {
                    "id": 1,
                    "model_id": "kerasccfraud",
                    "model_version": "df0c6c5e-e0ee-41bc-9d6d-57ace8552b8d",
                    "models_pk_id": 1,
                    "sha": "bc85ce596945f876256f41515c7501c399fd97ebcb9ab3dd41bf03f8937b4507",
                    "file_name": "keras_ccfraud.onnx",
                    "image_path": None,
                    "updated_at": "2022-10-26T14:12:41.040083+00:00",
                    "visibility": "private",
                    "owner_id": '""',
                }
            ],
            "workspace": {
                "id": 1,
                "name": "test - Default Workspace",
            },
        }

        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/models/get").mock(
            return_value=httpx.Response(200, json=example_models_1)
        )

        assert models[0].id() == 1
        assert models[0].name() == example_models_1["name"]

    @respx.mock(assert_all_mocked=True)
    def test_get_workspace_get_existing(self, respx_mock):
        workspace_name = "test-workspace"

        # Mock the list_workspaces method to return a workspace with the given name
        self.add_list_workspace_responder(respx_mock)
        # Call the get_workspace method
        ws = self.test_client.get_workspace(name=workspace_name)

        # Assert that the returned workspace is the one with the given name
        assert ws.name() == workspace_name

    @respx.mock(assert_all_mocked=True)
    def test_get_workspace_when_no_workspace_by_name_exist(self, respx_mock):
        workspace_name = "new-workspace"

        self.add_list_workspace_responder_with_no_workspaces(respx_mock)
        with pytest.raises(Exception) as error:
            self.test_client.get_workspace(
                name=workspace_name, create_if_not_exist=False
            )

        expected_string = (
            "Error: Workspace with name new-workspace does not exist."
            " If you would like to create one, send in the request with `create_if_not_exist` flag set to True."
        )
        assert expected_string == str(error.value)

    @respx.mock(assert_all_mocked=True)
    def test_get_workspace_creates_new_workspace_if_not_exists(self, respx_mock):
        workspace_name = "test-workspace-1"

        self.add_list_workspace_responder_with_no_workspaces(respx_mock)
        self.add_create_workspace_responder(respx_mock=respx_mock, expected_id=1)
        add_get_workspace_by_id_responder(respx_mock, self.test_client.api_endpoint, 1)
        ws = self.test_client.get_workspace(
            name=workspace_name, create_if_not_exist=True
        )

        assert ws.id() == 1
        assert ws.name() == workspace_name

    @respx.mock(assert_all_mocked=True)
    def test_get_workspace_errors_when_create_if_not_exist_is_not_boolean_true(
        self, respx_mock
    ):
        workspace_name = "test-workspace"

        self.add_list_workspace_responder_with_no_workspaces(respx_mock)
        with pytest.raises(Exception):
            self.test_client.get_workspace(
                name=workspace_name, create_if_not_exist="yes"
            )
