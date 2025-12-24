import datetime

import httpx
import respx
from dateutil import parser as dateparse

import wallaroo
from wallaroo.model import Model

from . import testutil
from .reusable_responders import (
    add_default_workspace_responder,
    add_list_models_responder,
)

example_model_version_1 = {
    "data": {
        "model_by_pk": {
            "id": 1,
            "model_id": "kerasccfraud",
            "model_version": "df0c6c5e-e0ee-41bc-9d6d-57ace8552b8d",
            "models_pk_id": 1,
            "sha": "bc85ce596945f876256f41515c7501c399fd97ebcb9ab3dd41bf03f8937b4507",
            "file_name": "keras_ccfraud.onnx",
            "image_path": None,
            "updated_at": "2022-10-26T14:12:41.040083+00:00",
            "visibility": "private",
        }
    }
}

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
model_dict_1 = {
    "id": 1,
    "name": "ccfraud",
    "owner_id": "bb2dec32-09a1-40fd-8b34-18bd61c9c070",
    "workspace_id": 1,
    "created_at": "2022-02-15T09:42:12.857637+00:00",
    "updated_at": "2022-02-15T09:42:12.857637+00:00",
}
model_dict_2 = {
    "id": 2,
    "name": "ccfraud",
    "owner_id": "bb2dec32-09a1-40fd-8b34-18bd61c9c070",
    "workspace_id": 2,
    "created_at": "2022-02-15T09:42:12.857637+00:00",
    "updated_at": "2022-02-15T09:42:12.857637+00:00",
}
model_version_dict = {
    "id": 1,
    "name": "variant-1",
    "visibility": "private",
    "workspace_id": 1,
    "status": "ready",
    "file_info": {
        "version": "ec1ab8e3-923b-40dd-9f77-f20bbe8058b3",
        "sha": "f7e49538e38bebe066ce8df97bac8be239ae8c7d2733e500c8cd633706ae95a8",
        "file_name": "simple_model.h5",
        "size": 100,
    },
}

model_list_resp_1 = {
    "models": [
        {
            "model": model_dict_1,
            "model_versions": [
                {
                    "model_version": model_version_dict,
                    "config": {
                        "id": 1,
                        "model_version_id": 1,
                        "runtime": "mlflow",
                    },
                },
            ],
            "workspace": {
                "id": 1,
                "name": "test Default Workspace 1",
                "archived": False,
                "created_at": "2022-02-15T09:42:12.857637+00:00",
            },
        },
        {
            "model": model_dict_2,
            "model_versions": [
                {
                    "model_version": model_version_dict,
                    "config": {
                        "id": 1,
                        "model_version_id": 1,
                        "runtime": "mlflow",
                    },
                },
            ],
            "workspace": {
                "id": 2,
                "name": "test-default-workspace-2",
                "archived": False,
                "created_at": "2022-02-15T09:42:12.857637+00:00",
            },
        },
    ]
}

model_list_resp_2 = {
    "models": [
        {
            "model": model_dict_2,
            "model_versions": [
                {
                    "model_version": model_version_dict,
                    "config": {
                        "id": 1,
                        "model_version_id": 1,
                        "runtime": "mlflow",
                    },
                },
            ],
            "workspace": {
                "id": 2,
                "name": "test-default-workspace-2",
                "archived": False,
                "created_at": "2022-02-15T09:42:12.857637+00:00",
            },
        },
    ]
}


class TestModel:
    def setup_method(self):
        self.api_endpoint = "http://api-lb"
        self.now = datetime.datetime.now()
        self.gql_client = testutil.new_gql_client(
            endpoint=f"{self.api_endpoint}/v1/graphql"
        )
        self.test_client = wallaroo.Client(
            api_endpoint=self.api_endpoint,
            gql_client=self.gql_client,
            request_timeout=2,
            interactive=False,
            auth_type="test_auth",
            config={"default_arch": "x86"},
        )

    @respx.mock(assert_all_mocked=True)
    def test_model_from_data(self, respx_mock):
        """Test that we can create a Models object directly by providing all the data."""

        m = Model(client=self.test_client, data=example_models_1)
        assert m.name() == example_models_1["name"]
        assert m.id() == example_models_1["id"]
        assert m.owner_id() == example_models_1["owner_id"]
        assert m.last_update_time() == dateparse.isoparse(
            example_models_1["updated_at"]
        )
        assert m.created_at() == dateparse.isoparse(example_models_1["created_at"])
        assert (
            m.versions()[0].version() == example_models_1["models"][0]["model_version"]
        )

    @respx.mock(assert_all_mocked=True)
    def test_model_from_mock(self, respx_mock):
        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/models/get").mock(
            return_value=httpx.Response(200, json=example_models_1)
        )

        m = Model(client=self.test_client, data={"id": 1})
        assert m.name() == example_models_1["name"]
        assert m.id() == example_models_1["id"]
        assert m.owner_id() == example_models_1["owner_id"]

    @respx.mock(assert_all_mocked=True)
    def test_list_models(self, respx_mock):
        add_default_workspace_responder(respx_mock, "http://api-lb")
        add_list_models_responder(
            respx_mock,
            self.test_client.api_endpoint,
            {"workspace_id": 1, "workspace_name": None},
            model_list_resp_1,
        )

        models = self.test_client.list_models()
        assert len(models) == 2
        assert models[0].name() == model_dict_1["name"]
        assert models[0].id() == model_dict_1["id"]
        assert models[0].owner_id() == model_dict_1["owner_id"]
