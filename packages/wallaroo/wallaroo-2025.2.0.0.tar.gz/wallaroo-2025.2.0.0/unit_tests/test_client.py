import json
import os
import string
import tempfile
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import cast
from unittest import mock
from unittest.mock import MagicMock, patch

# This file uses unittest, not pytest, so it can't use the pytest.mark fixture
import httpx
import pyarrow as pa
import pytest
import respx

import wallaroo
from wallaroo.engine_config import (
    Acceleration,
    ModelOptimizationConfigError,
    QaicConfig,
    QaicWithConfig,
)
from wallaroo.framework import CustomConfig, Framework, VLLMConfig
from wallaroo.model_version import ModelVersion
from wallaroo.object import (
    InvalidNameError,
)
from wallaroo.pipeline import Pipeline
from wallaroo.user import User

from . import testutil
from .reusable_responders import (
    add_default_workspace_responder,
    add_get_configured_model,
    add_get_model_by_id_responder,
    add_get_model_config_response,
    add_get_pipeline_by_id_responder,
    add_get_workspace_by_id_responder,
    add_insert_model_config_response,
    add_list_models_responder,
    add_list_tags_responder,
    add_pipeline_by_id_responder,
    add_pipeline_variant_by_id_responder,
    add_tag_by_id_responder,
)

with open("unit_tests/outputs/get_assay_results.json", "r") as fp:
    SAMPLE_GET_ASSAYS_RESULTS = json.loads(fp.read())

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


@pytest.fixture(autouse=True)
def enable_assay_v1():
    with mock.patch.dict(os.environ, {"ASSAYS_V2_ENABLED": "false"}):
        yield


class TestClientUrls:
    def setup_method(self) -> None:
        self.api_endpoint = "http://api-lb:8080"
        self.auth_type = "sso"

    def test_compute_urls_raises_error_when_passed_in_none(self):
        with pytest.raises(ValueError):
            wallaroo.client.Client.get_urls(None, self.api_endpoint)
        with pytest.raises(ValueError):
            wallaroo.client.Client.get_urls(self.auth_type, None)

    @mock.patch.dict(os.environ, {"WALLAROO_SDK_AUTH_TYPE": "user_password"})
    def test_compute_urls_get_auth_type_from_env_var(self):
        (auth_type, api_endpoint) = wallaroo.client.Client.get_urls(
            None, self.api_endpoint
        )

        assert auth_type == "user_password"
        assert api_endpoint == self.api_endpoint

    @mock.patch.dict(os.environ, {"WALLAROO_URL": "http://my-new-api-endpoint:8080"})
    def test_compute_urls_get_api_endpoint_from_env_vars(self):
        (auth_type, api_endpoint) = wallaroo.client.Client.get_urls(
            self.auth_type, None
        )
        assert auth_type == self.auth_type
        assert api_endpoint == "http://my-new-api-endpoint:8080"

    @mock.patch.dict(
        os.environ,
        {
            "WALLAROO_SDK_AUTH_TYPE": "user_password",
            "WALLAROO_URL": "http://my-new-api-endpoint:8080",
        },
    )
    def test_get_urls_user_input_overrides_env_vars(self):
        (auth_type, api_endpoint) = wallaroo.client.Client.get_urls(
            self.auth_type, self.api_endpoint
        )
        assert auth_type == self.auth_type
        assert api_endpoint == self.api_endpoint


class TestClient:
    def setup_method(self):
        self.now = datetime.now()
        self.gql_client = testutil.new_gql_client(
            endpoint="http://api-lb:8080/v1/graphql"
        )

        self.test_client = wallaroo.Client(
            gql_client=self.gql_client,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )

    def add_list_assays_responder(self, respx_mock):
        assay_resp = [
            {
                "id": 2,
                "name": "Assay 965409",
                "active": True,
                "status": '{"run_at": "2022-08-17T14:48:34.239664761+00:00",  "num_ok": 17, "num_warnings": 0, "num_alerts": 13}',
                "warning_threshold": None,
                "alert_threshold": 0.25,
                "pipeline_id": 15,
                "pipeline_name": "modelinsightse2e06104",
                "last_run": "2022-08-17T14:48:34.239665+00:00",
                "next_run": "2022-08-17T00:00:00+00:00",
                "run_until": None,
                "updated_at": "2022-08-17T14:48:30.962965+00:00",
                "workspace_id": 1,
                "workspace_name": "test - Default Workspace",
            },
            {
                "id": 1,
                "name": "Assay 109990",
                "active": True,
                "status": '{"run_at": "2022-08-16T14:31:59.750085918+00:00",  "num_ok": 17, "num_warnings": 0, "num_alerts": 13}',
                "warning_threshold": None,
                "alert_threshold": 0.25,
                "pipeline_id": 3,
                "pipeline_name": "mypipeline",
                "last_run": "2022-08-16T14:31:59.750086+00:00",
                "next_run": "2022-08-17T00:00:00+00:00",
                "run_until": None,
                "updated_at": "2022-08-16T14:31:57.956613+00:00",
                "workspace_id": 1,
                "workspace_name": "test - Default Workspace",
            },
        ]

        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/assays/list").mock(
            return_value=httpx.Response(200, json=assay_resp)
        )

    def add_user_responder(self, respx_mock):
        users_resp = {
            "users": {
                "a6fa51c3-532b-410a-a5b2-c79277f90e45": {
                    "id": "a6fa51c3-532b-410a-a5b2-c79277f90e45",
                    "createdTimestamp": 1649782475369,
                    "username": "ci",
                    "enabled": True,
                    "totp": False,
                    "emailVerified": True,
                    "firstName": "c",
                    "lastName": "i",
                    "email": "ci@x.com",
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
                "6934dc86-0953-4d0a-9de6-3825a19c3ab9": {
                    "id": "6934dc86-0953-4d0a-9de6-3825a19c3ab9",
                    "createdTimestamp": 1649782764151,
                    "username": "di",
                    "enabled": True,
                    "totp": False,
                    "emailVerified": False,
                    "firstName": "d",
                    "lastName": "i",
                    "email": "di@z.z",
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
            }
        }
        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/users/query").mock(
            return_value=httpx.Response(200, json=users_resp)
        )

    def test_given_config(self):
        import wallaroo.config as wallaroo_config

        _config = wallaroo_config._config
        assert self.test_client
        assert "x86" == _config["default_arch"]

    @respx.mock(assert_all_mocked=True)
    def test_list_models(self, respx_mock):
        add_default_workspace_responder(respx_mock)

        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/models/list").mock(
            return_value=httpx.Response(200, json=model_list_resp_1)
        )

        variants = self.test_client.list_models()

        assert 2 == len(variants)

    @respx.mock(assert_all_mocked=True)
    def test_list_models_filtered_by_workspace(self, respx_mock):
        add_default_workspace_responder(respx_mock)

        # No filtering, still filters by default workspace_id
        add_list_models_responder(
            respx_mock,
            self.test_client.api_endpoint,
            {"workspace_id": 1, "workspace_name": None},
            model_list_resp_1,
        )
        models_1 = self.test_client.list_models()
        assert 2 == len(models_1)

        # Filtering by workspace_id
        add_list_models_responder(
            respx_mock,
            self.test_client.api_endpoint,
            {"workspace_id": 2, "workspace_name": None},
            model_list_resp_2,
        )
        models_2 = self.test_client.list_models(workspace_id=2)
        assert 1 == len(models_2)

        # Filtering only by workspace_name
        add_list_models_responder(
            respx_mock,
            self.test_client.api_endpoint,
            {"workspace_id": None, "workspace_name": "test-default-workspace-2"},
            model_list_resp_2,
        )
        models_2 = self.test_client.list_models(
            workspace_name="test-default-workspace-2"
        )
        assert 1 == len(models_2)

    def test_list_tags(self, respx_mock):
        add_list_tags_responder(respx_mock, self.test_client.api_endpoint)
        add_tag_by_id_responder(respx_mock, self.test_client.api_endpoint)

        tags = self.test_client.list_tags()
        assert 1 == len(tags)
        assert 1 == len(respx_mock.calls)

    def test_list_deployments(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("ListDeployments"),
        ).mock(
            return_value=httpx.Response(
                200, json={"data": {"deployment": [{"id": 1}, {"id": 2}]}}
            )
        )

        deployments = self.test_client.list_deployments()

        assert 2 == len(deployments)
        assert 1 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=True)
    def test_model_version_by_name(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("ModelByName"),
        ).mock(return_value=httpx.Response(200, json={"data": {"model": [{"id": 1}]}}))

        variant = self.test_client.model_version_by_name(
            model_class="ccfraud", model_name="variant-1"
        )

        assert 1 == variant.id()
        assert 1 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=True)
    def test_deployment_by_name(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("DeploymentByName"),
        ).mock(
            return_value=httpx.Response(200, json={"data": {"deployment": [{"id": 1}]}})
        )

        deployment = self.test_client.deployment_by_name(
            deployment_name="ccfraud-deployment-1"
        )

        assert 1 == deployment.id()
        assert 1 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=True)
    def test_upload_model_stream(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/models/upload",
        ).mock(
            return_value=httpx.Response(
                200, json={"insert_models": {"returning": [{"models": [{"id": 1}]}]}}
            )
        )

        add_default_workspace_responder(respx_mock)
        add_get_configured_model(respx_mock, self.test_client.api_endpoint)

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"model_data")

            # Are we sanitizing inputs?
            try:
                variant = self.test_client.upload_model(
                    "hello world", f.name, Framework.TENSORFLOW
                )
            except InvalidNameError:
                pass
            else:
                self.assert_(False)

            # Correct case
            variant = self.test_client.upload_model("foo", f.name, Framework.TENSORFLOW)

        assert 1 == variant.id()
        assert 3 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=True)
    def test_upload_model_and_wait_for_convert(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/models/upload_and_convert",
        ).mock(
            return_value=httpx.Response(
                200, json={"insert_models": {"returning": [{"models": [{"id": 1}]}]}}
            )
        )
        add_get_configured_model(respx_mock)
        add_default_workspace_responder(respx_mock)

        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("ModelById"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "model_by_pk": {
                            "id": 1,
                            "sha": "adsfadsf",
                            "model_id": "some_model_name",
                            "model_version": "some_model_variant_name",
                            "status": "ready",
                            "file_name": "some_model_file.onnx",
                            "updated_at": self.now.isoformat(),
                            "visibility": "private",
                        },
                    },
                },
            ),
        )
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"model_data")

            variant = self.test_client.upload_model(
                name="foo",
                path=f.name,
                framework=Framework.KERAS,
                convert_wait=True,
                input_schema=pa.schema([]),
                output_schema=pa.schema([]),
            )

        assert 1 == variant.id()
        assert "ready" == variant.status()
        assert 5 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=True)
    def test_upload_model_and_wait_for_convert_timedout(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/models/upload_and_convert",
        ).mock(
            return_value=httpx.Response(
                200, json={"insert_models": {"returning": [{"models": [{"id": 1}]}]}}
            )
        )
        add_get_configured_model(
            respx_mock, self.test_client.api_endpoint, "pendingconversion"
        )
        add_default_workspace_responder(respx_mock)
        wallaroo.client.DEFAULT_MODEL_CONVERSION_TIMEOUT = 0.1

        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("ModelById"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "model_by_pk": {
                            "id": 1,
                            "sha": "adsfadsf",
                            "model_id": "some_model_name",
                            "model_version": "some_model_variant_name",
                            "status": "pendingconversion",
                            "file_name": "some_model_file.onnx",
                            "updated_at": self.now.isoformat(),
                            "visibility": "private",
                        },
                    },
                },
            ),
        )

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"model_data")

            # Now the method should return a model version object instead of raising an exception
            variant = self.test_client.upload_model(
                name="foo",
                path=f.name,
                framework=Framework.KERAS,
                convert_wait=True,
                input_schema=pa.schema([]),
                output_schema=pa.schema([]),
            )

            # Verify we got a model object back
            assert variant is not None
            assert 1 == variant.id()

            # Verify the error was stored on the model
            assert hasattr(variant, "_wait_error")
            assert variant._wait_error is not None
            assert "timed out" in str(variant._wait_error).lower()

        assert 5 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=True)
    def test_upload_model_and_wait_for_convert_error(self, respx_mock, capsys):
        """Test that model upload returns model object even when conversion fails"""
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/models/upload_and_convert",
        ).mock(
            return_value=httpx.Response(
                200, json={"insert_models": {"returning": [{"models": [{"id": 1}]}]}}
            )
        )
        add_get_configured_model(respx_mock, self.test_client.api_endpoint, "error")
        add_default_workspace_responder(respx_mock)

        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("ModelById"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "model_by_pk": {
                            "id": 1,
                            "sha": "adsfadsf",
                            "model_id": "some_model_name",
                            "model_version": "some_model_variant_name",
                            "status": "error",
                            "file_name": "some_model_file.onnx",
                            "updated_at": self.now.isoformat(),
                            "visibility": "private",
                        },
                    },
                },
            ),
        )

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"model_data")

            # Should return model version object instead of raising exception
            variant = self.test_client.upload_model(
                name="foo",
                path=f.name,
                framework=Framework.KERAS,
                convert_wait=True,
                input_schema=pa.schema([]),
                output_schema=pa.schema([]),
            )

            # Verify we got a model version object
            assert variant is not None
            assert 1 == variant.id()

            # Verify the error was stored on the model version
            assert hasattr(variant, "_wait_error")
            assert variant._wait_error is not None
            assert "conversion" in str(variant._wait_error).lower()

        # Verify the error was printed to stdout/stderr with red formatting
        captured = capsys.readouterr()
        assert (
            "conversion" in captured.out.lower() or "conversion" in captured.err.lower()
        )
        # Check for ANSI red color codes in the output
        assert (
            "\033[91m" in captured.out or "\033[91m" in captured.err
        ), "Error message should be printed in red"

        assert 5 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=True)
    def test_upload_model_and_convert(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/models/upload_and_convert",
        ).mock(
            return_value=httpx.Response(
                200, json={"insert_models": {"returning": [{"models": [{"id": 1}]}]}}
            )
        )

        add_get_configured_model(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock)

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"model_data")

            try:
                variant = self.test_client.upload_model(
                    name="hello world",
                    path=f.name,
                    framework=Framework.KERAS,
                    convert_wait=False,
                    input_schema=pa.schema([]),
                    output_schema=pa.schema([]),
                )
            except InvalidNameError:
                pass
            else:
                self.assert_(False)

            # Correct case
            variant = self.test_client.upload_model(
                name="foo",
                path=f.name,
                framework=Framework.KERAS,
                convert_wait=False,
                input_schema=pa.schema([]),
                output_schema=pa.schema([]),
            )

        assert 1 == variant.id()
        assert 3 == len(respx_mock.calls)

    @pytest.mark.parametrize(
        "accel",
        [
            Acceleration.QAIC,
            QaicWithConfig(),
            Acceleration.QAIC.with_config(QaicConfig()),
            Acceleration.CUDA,
            Acceleration.OpenVINO,
            Acceleration._None,
        ],
    )
    @respx.mock(assert_all_mocked=True)
    def test_upload_model_with_accel_config(self, accel, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/models/upload_and_convert",
        ).mock(
            return_value=httpx.Response(
                200, json={"insert_models": {"returning": [{"models": [{"id": 1}]}]}}
            )
        )
        add_get_configured_model(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock)

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"model_data")

            variant = self.test_client.upload_model(
                name="foo",
                path=f.name,
                framework=Framework.KERAS,
                convert_wait=False,
                input_schema=pa.schema([]),
                output_schema=pa.schema([]),
                accel=accel,
            )

        assert 1 == variant.id()
        assert 3 == len(respx_mock.calls)

    @pytest.mark.parametrize(
        "accel,config",
        [
            (Acceleration.QAIC, None),
            (Acceleration.CUDA, None),
            (Acceleration.CUDA, QaicConfig()),
            (Acceleration.OpenVINO, None),
            (Acceleration.OpenVINO, QaicConfig()),
            (Acceleration._None, None),
            (Acceleration._None, QaicConfig()),
        ],
    )
    @respx.mock(assert_all_mocked=True)
    def test_upload_model_with_invalid_accel_config(self, accel, config, respx_mock):
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"model_data")

            with pytest.raises(
                ModelOptimizationConfigError,
                match="The specified model optimization configuration is not available. "
                "Please try this operation again using a different configuration "
                "or contact Wallaroo at support@wallaroo.ai for questions or help.",
            ):
                _ = self.test_client.upload_model(
                    name="foo",
                    path=f.name,
                    framework=Framework.KERAS,
                    convert_wait=True,
                    input_schema=pa.schema([]),
                    output_schema=pa.schema([]),
                    accel=accel.with_config(config),
                )

    @pytest.mark.parametrize(
        "framework,config",
        [
            (Framework.KERAS, None),
            (Framework.VLLM, None),
            (Framework.VLLM, VLLMConfig()),
            (Framework.CUSTOM, None),
            (Framework.CUSTOM, CustomConfig()),
        ],
    )
    @respx.mock(assert_all_mocked=True)
    def test_upload_model_with_framework_config(self, framework, config, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/models/upload_and_convert",
        ).mock(
            return_value=httpx.Response(
                200, json={"insert_models": {"returning": [{"models": [{"id": 1}]}]}}
            )
        )
        add_get_configured_model(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock)

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"model_data")

            variant = self.test_client.upload_model(
                name="foo",
                path=f.name,
                framework=framework,
                convert_wait=False,
                input_schema=pa.schema([]),
                output_schema=pa.schema([]),
            )

        assert 1 == variant.id()
        assert 3 == len(respx_mock.calls)

    @pytest.mark.parametrize(
        "framework,config",
        [
            (Framework.CUSTOM, VLLMConfig()),
            (Framework.VLLM, CustomConfig()),
            (Framework.KERAS, VLLMConfig()),
            (Framework.KERAS, CustomConfig()),
        ],
    )
    @respx.mock(assert_all_mocked=True)
    def test_upload_model_with_invalid_framework_config(
        self, framework, config, respx_mock
    ):
        with tempfile.NamedTemporaryFile() as f:
            f.write(b"model_data")

            with pytest.raises(
                ModelOptimizationConfigError,
                match="The specified model optimization configuration is not available. "
                "Please try this operation again using a different configuration "
                "or contact Wallaroo at support@wallaroo.ai for questions or help.",
            ):
                _ = self.test_client.upload_model(
                    name="foo",
                    path=f.name,
                    framework=framework,
                    convert_wait=True,
                    input_schema=pa.schema([]),
                    output_schema=pa.schema([]),
                    framework_config=config,
                )

    @respx.mock(assert_all_mocked=True)
    def test_register_mlflow_model(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/models/upload",
        ).mock(
            return_value=httpx.Response(
                200, json={"insert_models": {"returning": [{"models": [{"id": 1}]}]}}
            )
        )
        add_get_configured_model(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock)
        add_insert_model_config_response(respx_mock)

        input_schema = pa.schema([pa.field("input", pa.list_(pa.float32(), 1))])
        output_schema = pa.schema([pa.field("output", pa.list_(pa.float32(), 1))])
        variant = self.test_client.register_model_image(
            "mlflow-model", "my-image"
        ).configure(
            "mlflow",
            input_schema=input_schema,
            output_schema=output_schema,
        )
        assert 1 == variant.id()
        assert 4 == len(respx_mock.calls)
        upload_call = next(
            call
            for call in respx_mock.calls
            if call.request.url.path == "/v1/api/models/upload"
        )
        assert upload_call.request.method == "POST"
        assert upload_call.request.headers["Content-Type"].startswith(
            "multipart/form-data"
        )

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_pipelines_by_name(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("PipelineByName"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"pipeline": [{"id": 1}, {"id": 2}]}},
            )
        )

        add_pipeline_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_get_workspace_by_id_responder(respx_mock, workspace_id=1)
        pipelines = self.test_client.pipelines_by_name(pipeline_name="pipeline-1")

        assert 2 == len(pipelines)
        assert 1 == pipelines[0].workspace().id()

    @respx.mock(assert_all_mocked=True)
    def test_list_pipelines_none(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/pipelines/list_pipelines"
        ).mock(return_value=httpx.Response(200, json={"pipelines": []}))

        pipelines = self.test_client.list_pipelines()
        assert pipelines == []
        assert pipelines._repr_html_() == "(no pipelines)"

    @respx.mock(assert_all_mocked=True)
    def test_list_pipelines(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/pipelines/list_pipelines"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "pipelines": [
                        {
                            "pipeline": {
                                "id": 1,
                                "name": "pipeline-2",
                                "created_at": "2022-04-18T13:55:16.880148+00:00",
                                "updated_at": "2022-04-18T13:55:16.915664+00:00",
                            },
                            "workspace": {
                                "id": 1,
                                "name": "test - default workspace 1",
                                "archived": False,
                                "created_by": "demo@wallaroo.ai",
                                "group_id": "1",
                                "created_at": "2022-04-18T13:55:16.880148+00:00",
                            },
                            "plateau_topic": "test-plateau-topic-1",
                        },
                        {
                            "pipeline": {
                                "id": 2,
                                "name": "pipeline-2",
                                "created_at": "2022-04-18T13:55:16.880148+00:00",
                                "updated_at": "2022-04-18T13:55:16.915664+00:00",
                            },
                            "workspace": {
                                "id": 2,
                                "name": "test - default workspace 2",
                                "archived": False,
                                "created_by": "demo@wallaroo.ai",
                                "group_id": "1",
                                "created_at": "2022-04-18T13:55:16.880148+00:00",
                            },
                            "plateau_topic": "test-plateau-topic-2",
                        },
                    ]
                },
            )
        )
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("PipelineById"),
        ).mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "data": {
                            "pipeline_by_pk": {
                                "id": 1,
                                "pipeline_id": "pipeline-1",
                                "created_at": "2022-04-18T13:55:16.880148+00:00",
                                "updated_at": "2022-04-18T13:55:16.915664+00:00",
                                "visibility": "private",
                                "owner_id": "'",
                                "pipeline_versions": [{"id": 2}],
                                "pipeline_tags": [
                                    {"tag": {"id": 1, "tag": "byhand222"}},
                                    {"tag": {"id": 2, "tag": "foo"}},
                                ],
                                "workspace": {
                                    "id": 1,
                                    "name": "test - default workspace 1",
                                },
                            }
                        }
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "data": {
                            "pipeline_by_pk": {
                                "id": 2,
                                "pipeline_id": "pipeline-2",
                                "created_at": "2022-04-18T13:55:16.880148+00:00",
                                "updated_at": "2022-04-18T13:55:16.915664+00:00",
                                "visibility": "private",
                                "owner_id": "'",
                                "pipeline_versions": [{"id": 2}],
                                "pipeline_tags": [
                                    {"tag": {"id": 1, "tag": "byhand222"}},
                                    {"tag": {"id": 2, "tag": "foo"}},
                                ],
                                "workspace": {
                                    "id": 2,
                                    "name": "test - default workspace 2",
                                },
                            }
                        }
                    },
                ),
            ]
        )

        pipelines = self.test_client.list_pipelines()

        # gets all pipelines from all workspaces
        assert 2 == len(pipelines)
        assert pipelines[0].workspace().id() == 1
        assert pipelines[0].workspace().name() == "test - default workspace 1"

        assert pipelines[1].workspace().id() == 2
        assert pipelines[1].workspace().name() == "test - default workspace 2"

    @respx.mock(assert_all_mocked=True)
    def test_list_pipelines_filter_by_workspace_id(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/pipelines/list_pipelines"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "pipelines": [
                        {
                            "pipeline": {
                                "id": 1,
                                "name": "pipeline-2",
                                "created_at": "2022-04-18T13:55:16.880148+00:00",
                                "updated_at": "2022-04-18T13:55:16.915664+00:00",
                            },
                            "workspace": {
                                "id": 1,
                                "name": "test - default workspace 1",
                                "archived": False,
                                "created_by": "demo@wallaroo.ai",
                                "group_id": "1",
                                "created_at": "2022-04-18T13:55:16.880148+00:00",
                            },
                            "plateau_topic": "test-plateau-topic-1",
                        }
                    ]
                },
            )
        )
        add_pipeline_by_id_responder(respx_mock, self.test_client.api_endpoint, 1)

        pipelines = self.test_client.list_pipelines(workspace_id=1)

        assert 1 == len(pipelines)
        assert pipelines[0].workspace().id() == 1
        assert pipelines[0].workspace().name() == "test - default workspace 1"

    @respx.mock(assert_all_mocked=True)
    def test_get_pipeline(self, respx_mock):
        add_get_workspace_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)
        add_get_pipeline_by_id_responder(respx_mock, self.test_client.api_endpoint)

        test_pipeline = self.test_client.get_pipeline(name="test-pipeline")
        assert isinstance(test_pipeline, Pipeline)
        # Doesn't set a specific version to deploy
        assert test_pipeline._pipeline_version_to_deploy is None

    @respx.mock(assert_all_mocked=True)
    def test_get_pipeline_specific_version(self, respx_mock):
        add_get_workspace_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)
        add_get_pipeline_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_pipeline_variant_by_id_responder(respx_mock, self.test_client.api_endpoint)

        test_pipeline = self.test_client.get_pipeline(
            name="test-pipeline", version="v1"
        )
        assert isinstance(test_pipeline, Pipeline)
        # Sets a specific version to deploy
        assert "v1" == test_pipeline._pipeline_version_to_deploy.name()

    @respx.mock(assert_all_mocked=True)
    def test_get_pipeline_when_pipeline_does_not_exist(self, respx_mock):
        add_get_workspace_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)
        add_get_pipeline_by_id_responder(respx_mock, self.test_client.api_endpoint)

        with pytest.raises(Exception) as error:
            self.test_client.get_pipeline(name="wrong-test-pipeline")

        expected_string = "Pipeline wrong-test-pipeline not found in this workspace."
        assert expected_string == str(error.value)

    @respx.mock(assert_all_mocked=True)
    def test_get_pipeline_specific_version_does_not_exist(self, respx_mock):
        add_get_workspace_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)
        add_get_pipeline_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_pipeline_variant_by_id_responder(respx_mock, self.test_client.api_endpoint)

        with pytest.raises(Exception) as error:
            self.test_client.get_pipeline(name="test-pipeline", version="v2")

        expected_string = "Pipeline version v2 not found in this workspace."
        assert expected_string == str(error.value)

    @respx.mock(assert_all_mocked=True)
    def test_build_pipeline(self, respx_mock):
        created_pipeline_pk_id = 1
        pipeline_creation_resp = {
            "pipeline_pk_id": created_pipeline_pk_id,
            "pipeline_variant_pk_id": 1,
            "pipeline_variant_version": 1,
        }
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/pipelines/create"
        ).mock(return_value=httpx.Response(200, json=pipeline_creation_resp))
        add_get_model_config_response(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)

        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("PipelineById"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "pipeline_by_pk": {
                            "id": 1,
                            "pipeline_id": "foo-278333879",
                            "created_at": "2022-02-01T18:42:27.592326+00:00",
                            "updated_at": "2022-02-01T18:42:34.055532+00:00",
                            "visibility": "private",
                            "pipeline_versions": [{"id": 2}, {"id": 1}],
                        }
                    }
                },
            ),
        )

        default_model = wallaroo.model_version.ModelVersion(
            self.test_client,
            data={
                "id": 1,
                "model_id": "ccfraud",
                "model_version": "default",
                "sha": "default_sha",
            },
        )
        experiment_model = wallaroo.model_version.ModelVersion(
            self.test_client,
            data={
                "id": 2,
                "model_id": "ccfraud",
                "model_version": "experiment",
                "sha": "experiment_sha",
            },
        )
        b = self.test_client.build_pipeline(
            "vse-pipeline",
        )
        b = b.add_key_split(default_model, "card_type", {"gold": experiment_model})
        pipeline = b._upload()

        assert created_pipeline_pk_id == pipeline.id()
        assert 6 == len(respx_mock.calls)

        # Are we sanitizing inputs?
        try:
            self.test_client.build_pipeline("not.quite.valid")
        except InvalidNameError:
            pass
        else:
            self.assert_(False)

    @respx.mock
    def test_list_users(self, respx_mock):
        self.add_user_responder(respx_mock)
        users = self.test_client.list_users()

        assert 2 == len(users)
        assert isinstance(users[0], User)
        assert isinstance(users[1], User)
        assert users[0].id() == "a6fa51c3-532b-410a-a5b2-c79277f90e45"
        assert users[0].username() == "ci"
        assert users[0].email() == "ci@x.com"

    @respx.mock(assert_all_mocked=True)
    def test_get_model(self, respx_mock):
        add_get_model_by_id_responder(respx_mock, self.test_client.api_endpoint, 2)
        add_get_workspace_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)
        example_models_1 = {
            "id": 1,
            "created_at": "2022-10-26T14:12:41.040083+00:00",
            "name": "test-model",
            "owner_id": '""',
            "updated_at": "2022-10-26T14:12:41.040083+00:00",
            "models": [
                {
                    "id": 2,
                    "model_id": "kerasccfraud",
                    "model_version": "v2",
                    "models_pk_id": 1,
                    "sha": "bc85ce596945f876256f41515c7501c399fd97ebcb9ab3dd41bf03f8937b4507",
                    "file_name": "keras_ccfraud.onnx",
                    "image_path": None,
                    "updated_at": "2022-10-27T14:12:41.040083+00:00",
                    "visibility": "private",
                    "owner_id": '""',
                },
                {
                    "id": 1,
                    "model_id": "kerasccfraud",
                    "model_version": "v1",
                    "models_pk_id": 1,
                    "sha": "bc85ce596945f876256f41515c7501c399fd97ebcb9ab3dd41bf03f8937b4507",
                    "file_name": "keras_ccfraud.onnx",
                    "image_path": None,
                    "updated_at": "2022-10-26T14:12:41.040083+00:00",
                    "visibility": "private",
                    "owner_id": '""',
                },
            ],
            "workspace": {
                "id": 1,
                "name": "test - Default Workspace",
            },
        }

        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/models/get").mock(
            return_value=httpx.Response(200, json=example_models_1)
        )
        test_model_version = self.test_client.get_model(name="test-model")
        assert isinstance(test_model_version, ModelVersion)
        # Default version is the latest
        assert test_model_version.version() == "v2"
        assert test_model_version.workspace().id() == 1

    @respx.mock(assert_all_mocked=True)
    def test_get_model_name_does_not_exist(self, respx_mock):
        add_get_workspace_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)
        example_models_1 = {
            "id": 1,
            "created_at": "2022-10-26T14:12:41.040083+00:00",
            "name": "test-model",
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
        }

        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/models/get").mock(
            return_value=httpx.Response(200, json=example_models_1)
        )
        with pytest.raises(Exception):
            self.test_client.get_model(name="test-model-does-not-exist")

    @respx.mock(assert_all_mocked=True)
    def test_get_model_specific_version(self, respx_mock):
        add_get_workspace_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)
        example_models_1 = {
            "id": 1,
            "created_at": "2022-10-26T14:12:41.040083+00:00",
            "name": "test-model",
            "owner_id": '""',
            "updated_at": "2022-10-26T14:12:41.040083+00:00",
            "models": [
                {
                    "id": 1,
                    "model_id": "kerasccfraud",
                    "model_version": "v1",
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
        test_model_version = self.test_client.get_model(name="test-model", version="v1")
        assert isinstance(test_model_version, ModelVersion)

    @respx.mock(assert_all_mocked=True)
    def test_get_model_specific_version_does_not_exist(self, respx_mock):
        add_get_workspace_by_id_responder(respx_mock, self.test_client.api_endpoint)
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)
        example_models_1 = {
            "id": 1,
            "created_at": "2022-10-26T14:12:41.040083+00:00",
            "name": "test-model",
            "owner_id": '""',
            "updated_at": "2022-10-26T14:12:41.040083+00:00",
            "models": [
                {
                    "id": 1,
                    "model_id": "kerasccfraud",
                    "model_version": "v1",
                    "models_pk_id": 1,
                    "sha": "bc85ce596945f876256f41515c7501c399fd97ebcb9ab3dd41bf03f8937b4507",
                    "file_name": "keras_ccfraud.onnx",
                    "image_path": None,
                    "updated_at": "2022-10-26T14:12:41.040083+00:00",
                    "visibility": "private",
                    "owner_id": '""',
                }
            ],
        }

        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/models/get").mock(
            return_value=httpx.Response(200, json=example_models_1)
        )
        with pytest.raises(Exception):
            self.test_client.get_model(name="test-model", version="v2")

    def test_generate_model_query_with_all_params(self):
        expected_query = """
            query GetModels($search_term: String!, $user_id: String!, $workspace_id: bigint!, $workspace_name: String!, $start_created_at: timestamptz!, $end_created_at: timestamptz!) {
              search_models(args: {search: $search_term}, where: {_and: [{owner_id: {_eq: $user_id}}, {model: {workspace: {_and: [{id: {_eq: $workspace_id}}, {name: {_eq: $workspace_name}}]}}}, {created_at: {_gte: $start_created_at, _lte: $end_created_at}}] }, order_by: {created_at: desc}) {
                id
              }
            }
        """
        start_datetime = self.now - timedelta(days=5)
        end_datetime = self.now
        expected_params = {
            "search_term": "model",
            "user_id": "5905c14f-c70d-4afb-a1ec-8fa69e8e5f35",
            "start_created_at": start_datetime.isoformat(),
            "end_created_at": end_datetime.isoformat(),
            "workspace_id": 1,
            "workspace_name": "test-workspace",
        }

        client = self.test_client
        (query, params) = client._generate_model_query(
            user_id="5905c14f-c70d-4afb-a1ec-8fa69e8e5f35",
            search_term="model",
            start=start_datetime,
            end=end_datetime,
            workspace_id=1,
            workspace_name="test-workspace",
        )
        assert query.translate(string.whitespace) == expected_query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_generate_model_query_with_no_start(self):
        expected_query = """
            query GetModels($search_term: String!, $user_id: String!, $end_created_at: timestamptz!) {
              search_models(args: {search: $search_term}, where: {_and: [{owner_id: {_eq: $user_id}}, {created_at: {_lte: $end_created_at}}] }, order_by: {created_at: desc}) {
                id
              }
            }
        """
        end_datetime = self.now
        expected_params = {
            "search_term": "model",
            "user_id": "5905c14f-c70d-4afb-a1ec-8fa69e8e5f35",
            "end_created_at": end_datetime.isoformat(),
        }

        client = self.test_client
        (query, params) = client._generate_model_query(
            user_id="5905c14f-c70d-4afb-a1ec-8fa69e8e5f35",
            search_term="model",
            end=end_datetime,
        )
        assert expected_query.translate(string.whitespace) == query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_generate_model_query_with_no_end(self):
        expected_query = """
            query GetModels($search_term: String!, $user_id: String!, $start_created_at: timestamptz!) {
              search_models(args: {search: $search_term}, where: {_and: [{owner_id: {_eq: $user_id}}, {created_at: {_gte: $start_created_at}}] }, order_by: {created_at: desc}) {
                id
              }
            }
        """
        start_datetime = self.now
        expected_params = {
            "search_term": "model",
            "user_id": "5905c14f-c70d-4afb-a1ec-8fa69e8e5f35",
            "start_created_at": start_datetime.isoformat(),
        }

        client = self.test_client
        (query, params) = client._generate_model_query(
            user_id="5905c14f-c70d-4afb-a1ec-8fa69e8e5f35",
            search_term="model",
            start=start_datetime,
        )
        assert expected_query.translate(string.whitespace) == query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_generate_model_query_with_no_params(self):
        expected_query = """
            query GetModels($search_term: String!) {
              search_models(args: {search: $search_term}, order_by: {created_at: desc}) {
                id
              }
            }
        """
        expected_params = {"search_term": ""}
        client = self.test_client
        (query, params) = client._generate_model_query()
        assert expected_query.translate(string.whitespace) == query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_generate_model_query_with_workspace_filters(self):
        expected_query = """
            query GetModels($search_term: String!, $workspace_id: bigint!, $workspace_name: String!) {
              search_models(args: {search: $search_term}, where: {model: {workspace: {_and: [{id: {_eq: $workspace_id}}, {name: {_eq: $workspace_name}}]}}}, order_by: {created_at: desc}) {
                id
              }
            }
        """
        expected_params = {
            "search_term": "model",
            "workspace_id": 1,
            "workspace_name": "test-workspace",
        }

        client = self.test_client
        (query, params) = client._generate_model_query(
            search_term="model",
            workspace_id=1,
            workspace_name="test-workspace",
        )
        assert expected_query.translate(string.whitespace) == query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_generate_pipelines_query_with_no_params(self):
        expected_query = """
            query GetPipelines($search_term: String!) {
                search_pipelines(args: {search: $search_term}, distinct_on: id, order_by: {id: desc}) {
                    id
                    created_at
                    pipeline_pk_id
                    updated_at
                    version
                    pipeline {
                        id
                        pipeline_id
                        pipeline_tags {
                            id
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
            }
        """

        expected_params = {"search_term": ""}
        client = self.test_client
        (query, params) = client._generate_search_pipeline_query()

        assert expected_query.translate(string.whitespace) == query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_generate_pipelines_query_with_workspace_filtering(self):
        expected_query = """
            query GetPipelines($search_term: String!, $workspace_id: bigint!, $workspace_name: String!) {
                search_pipelines(args: {search: $search_term}, distinct_on: id, where: {pipeline: {workspace: {_and: [{id: {_eq: $workspace_id}}, {name: {_eq: $workspace_name}}]}}}, order_by: {id: desc}) {
                    id
                    created_at
                    pipeline_pk_id
                    updated_at
                    version
                    pipeline {
                        id
                        pipeline_id
                        pipeline_tags {
                            id
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
            }
        """

        expected_params = {
            "search_term": "",
            "workspace_id": 1,
            "workspace_name": "test_workspace",
        }
        client = self.test_client
        (query, params) = client._generate_search_pipeline_query(
            workspace_id=1, workspace_name="test_workspace"
        )

        assert query.translate(string.whitespace) == expected_query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_generate_pipelines_query_with_user(self):
        expected_query = """
            query GetPipelines($search_term: String!, $user_id: String!) {
                search_pipelines(args: {search: $search_term}, distinct_on: id, where: {owner_id: {_eq: $user_id}}, order_by: {id: desc}) {
                    id
                    created_at
                    pipeline_pk_id
                    updated_at
                    version
                    pipeline {
                        id
                        pipeline_id
                        pipeline_tags {
                            id
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
            }
        """
        expected_params = {"search_term": "", "user_id": "my_id"}
        client = self.test_client
        (query, params) = client._generate_search_pipeline_query(user_id="my_id")

        assert expected_query.translate(string.whitespace) == query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_generate_pipelines_query_with_deployed(self):
        expected_query = """
            query GetPipelines($search_term: String!, $user_id: String!, $deployed: Boolean!) {
                search_pipelines(args: {search: $search_term}, distinct_on: id, where: {_and: [{owner_id: {_eq: $user_id}}, {pipeline: {deployment: {deployed: {_eq: $deployed}}}}] }, order_by: {id: desc}) {
                    id
                    created_at
                    pipeline_pk_id
                    updated_at
                    version
                    pipeline {
                        id
                        pipeline_id
                        pipeline_tags {
                            id
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
            }
        """
        expected_params = {"search_term": "", "user_id": "my_id", "deployed": True}
        client = self.test_client
        (query, params) = client._generate_search_pipeline_query(
            user_id="my_id", deployed=True
        )

        assert expected_query.translate(string.whitespace) == query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_generate_pipelines_query_with_created_at(self):
        expected_query = """
            query GetPipelines($search_term: String!, $user_id: String!, $start_created_at: timestamptz!) {
                search_pipelines(args: {search: $search_term}, distinct_on: id, where: {_and: [{owner_id: {_eq: $user_id}}, {created_at: {_gte: $start_created_at}}] }, order_by: {id: desc}) {
                    id
                    created_at
                    pipeline_pk_id
                    updated_at
                    version
                    pipeline {
                        id
                        pipeline_id
                        pipeline_tags {
                            id
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
            }
        """
        start_datetime = self.now
        expected_params = {
            "search_term": "",
            "user_id": "my_id",
            "start_created_at": start_datetime.isoformat(),
        }
        client = self.test_client
        (query, params) = client._generate_search_pipeline_query(
            user_id="my_id", created_start=start_datetime
        )

        assert expected_query.translate(string.whitespace) == query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_generate_pipelines_query_with_updated_at(self):
        expected_query = """
            query GetPipelines($search_term: String!, $user_id: String!, $start_created_at: timestamptz!, $start_updated_at: timestamptz!, $end_updated_at: timestamptz!) {
                search_pipelines(args: {search: $search_term}, distinct_on: id, where: {_and: [{owner_id: {_eq: $user_id}}, {created_at: {_gte: $start_created_at}}, {updated_at: {_gte: $start_updated_at, _lte: $end_updated_at}}] }, order_by: {id: desc}) {
                    id
                    created_at
                    pipeline_pk_id
                    updated_at
                    version
                    pipeline {
                        id
                        pipeline_id
                        pipeline_tags {
                            id
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
            }
        """
        start_datetime = self.now - timedelta(days=5)
        updated_datetime = self.now - timedelta(days=1)
        end_datetime = self.now
        expected_params = {
            "search_term": "",
            "user_id": "my_id",
            "start_created_at": start_datetime.isoformat(),
            "start_updated_at": updated_datetime.isoformat(),
            "end_updated_at": end_datetime.isoformat(),
        }
        client = self.test_client
        (query, params) = client._generate_search_pipeline_query(
            user_id="my_id",
            created_start=start_datetime,
            updated_start=updated_datetime,
            updated_end=end_datetime,
        )

        assert expected_query.translate(string.whitespace) == query.translate(
            string.whitespace
        )
        assert expected_params == params

    def test_jupyter_client(self):
        with patch.dict(
            "os.environ",
            {
                "JUPYTER_SVC_SERVICE_HOST": "x://yz",
                "WALLAROO_URL": "http://api-lb:8080",
            },
        ):
            client = wallaroo.Client(
                auth_type="test_auth", config={"default_arch": "x86"}
            )
            assert client._interactive == True

            client = wallaroo.Client(
                interactive=True, auth_type="test_auth", config={"default_arch": "x86"}
            )
            assert client._interactive == True

            client = wallaroo.Client(
                interactive=False, auth_type="test_auth", config={"default_arch": "x86"}
            )
            assert client._interactive == False

    def test_non_jupyter_client(self):
        mockenv = os.environ
        mockenv["WALLAROO_URL"] = "http://api-lb:8080"
        if "JUPYTER_SVC_SERVICE_HOST" in mockenv:
            del mockenv["JUPYTER_SVC_SERVICE_HOST"]

        with patch.dict("os.environ", mockenv):
            client = self.test_client
            assert client._interactive == False

            client = wallaroo.Client(
                interactive=True, auth_type="test_auth", config={"default_arch": "x86"}
            )
            assert client._interactive == True

            client = wallaroo.Client(
                interactive=False, auth_type="test_auth", config={"default_arch": "x86"}
            )
            assert client._interactive == False

    @respx.mock(assert_all_mocked=True)
    def test_search_pipelines_none(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("GetPipelines"),
        ).mock(
            return_value=httpx.Response(200, json={"data": {"search_pipelines": []}})
        )

        result = self.test_client.search_pipeline_versions()
        assert result == []
        assert result._repr_html_() == "(no pipelines)"

    @respx.mock(assert_all_mocked=True)
    def test_list_assays_none(self, respx_mock):
        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/assays/list").mock(
            return_value=httpx.Response(200, json=[])
        )

        assays = self.test_client.list_assays()
        assert assays == []
        assert assays._repr_html_() == "(No Assays)"

    @respx.mock(assert_all_mocked=True)
    def test_list_assays(self, respx_mock):
        self.add_list_assays_responder(respx_mock)
        assays = self.test_client.list_assays()

        assert 2 == len(assays)
        assert 2 == assays[0]._id
        assert "Assay 965409" == assays[0]._name
        assert 15 == assays[0]._pipeline_id
        assert "mypipeline" == assays[1]._pipeline_name
        html = assays._repr_html_()
        assert "</table>" in html
        assert "<td>mypipeline</td>" in html

    @respx.mock(assert_all_mocked=True)
    def test_get_assay_results(self, respx_mock):
        resp = respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/get_assay_results"
        ).mock(return_value=httpx.Response(200, json=SAMPLE_GET_ASSAYS_RESULTS))
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/get_assay_by_id"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 27,
                    "name": "getassayinfotest",
                    "active": True,
                    "status": '{"run_at": "2024-02-26T03:03:46.393130216+00:00",  "num_ok": 1, "num_warnings": 0, "num_alerts": 1}',
                    "alert_threshold": 0.25,
                    "pipeline_id": 1,
                    "pipeline_name": "assay-demonstration-tutorial-5",
                    "workspace_id": 1,
                    "workspace_name": "test_workspace",
                    "next_run": "2024-02-26T03:03:37.290182+00:00",
                    "warning_threshold": None,
                    "last_run": "2024-02-26T03:03:46.39313+00:00",
                    "run_until": "2024-02-26T03:03:39.507103+00:00",
                    "created_at": "2024-02-26T03:03:46.183491+00:00",
                    "updated_at": "2024-02-26T03:03:46.183491+00:00",
                    "baseline": {
                        "static": {
                            "count": 500,
                            "min": 236238.65625,
                            "max": 1412215.25,
                            "mean": 514178.5481875,
                            "median": 449699.75,
                            "std": 229036.31316679736,
                            "edges": [
                                236238.65625,
                                311515.125,
                                437177.84375,
                                513583.125,
                                684577.1875,
                                1412215.25,
                                None,
                            ],
                            "edge_names": [
                                "left_outlier",
                                "q_20",
                                "q_40",
                                "q_60",
                                "q_80",
                                "q_100",
                                "right_outlier",
                            ],
                            "aggregated_values": [
                                0.0,
                                0.2,
                                0.224,
                                0.18,
                                0.196,
                                0.2,
                                0.0,
                            ],
                            "aggregation": "Density",
                            "start": None,
                            "end": None,
                        }
                    },
                    "window": {
                        "model_name": "house-price-estimator",
                        "path": "output variable 0",
                        "pipeline_name": "assay-demonstration-tutorial-5",
                        "width": "1 minutes",
                        "workspace_id": 2,
                        "interval": "1 minutes",
                        "start": "2024-02-26T02:56:37.290182+00:00",
                        "locations": [],
                    },
                    "summarizer": {
                        "bin_mode": "Quantile",
                        "aggregation": "Density",
                        "metric": "PSI",
                        "num_bins": 5,
                        "type": "UnivariateContinuous",
                        "bin_weights": None,
                        "provided_edges": None,
                    },
                },
            )
        )
        # naive dates
        start_date = datetime(2023, 10, 11, 0, 0, 0, 0)
        end_date = datetime(2023, 10, 13, 0, 0, 0, 0)

        # tz aware dates
        start_date_utc = start_date.astimezone(tz=timezone.utc)
        end_date_utc = end_date.astimezone(tz=timezone.utc)

        assay_results = self.test_client.get_assay_results(
            assay_id=27, start=start_date, end=end_date
        )

        # Check that the request was made with the correct parameters - verify dates are tz aware
        response_params = json.loads(resp.calls.last.request.content.decode("utf8"))
        assert {
            "assay_id": 27,
            "start": start_date_utc.isoformat(),
            "end": end_date_utc.isoformat(),
            "workspace_id": None,
            "workspace_name": None,
        } == response_params

        # Check that the response was parsed correctly
        assert len(assay_results) == 2
        assert assay_results[0].assay_id == 27
        assert assay_results[0].id == 41
        assay_results_df = assay_results.to_dataframe()
        assert assay_results_df["assay_name"].iloc[0] == "getassayinfotest"
        assert (
            assay_results_df["pipeline_name"].iloc[0]
            == "assay-demonstration-tutorial-5"
        )
        assert assay_results_df["iopath"].iloc[0] == "output variable 0"

    @respx.mock(assert_all_mocked=True, assert_all_called=True)
    def test_set_assay_active(self, respx_mock):
        turn_on_payload = {"id": 1, "active": True}
        turn_off_payload = {"id": 1, "active": False}
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/set_active",
            json=turn_on_payload,
        ).mock(return_value=httpx.Response(200, json=turn_on_payload))

        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/set_active",
            json=turn_off_payload,
        ).mock(return_value=httpx.Response(200, json=turn_off_payload))

        self.test_client.set_assay_active(1, True)
        self.test_client.set_assay_active(1, False)

    @respx.mock()
    def test_get_assay_info_for_assay_built_with_uploaded_file(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/get_assay_by_id",
            json={"id": 1, "workspace_id": None, "workspace_name": None},
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1,
                    "name": "getassayinfotest",
                    "active": True,
                    "status": '{"run_at": "2024-02-26T03:03:46.393130216+00:00",  "num_ok": 1, "num_warnings": 0, "num_alerts": 1}',
                    "alert_threshold": 0.25,
                    "pipeline_id": 1,
                    "pipeline_name": "assay-demonstration-tutorial-5",
                    "workspace_id": 1,
                    "workspace_name": "test_workspace",
                    "next_run": "2024-02-26T03:03:37.290182+00:00",
                    "warning_threshold": None,
                    "last_run": "2024-02-26T03:03:46.39313+00:00",
                    "run_until": "2024-02-26T03:03:39.507103+00:00",
                    "created_at": "2024-02-26T03:03:46.183491+00:00",
                    "updated_at": "2024-02-26T03:03:46.183491+00:00",
                    "baseline": {
                        "static": {
                            "count": 500,
                            "min": 236238.65625,
                            "max": 1412215.25,
                            "mean": 514178.5481875,
                            "median": 449699.75,
                            "std": 229036.31316679736,
                            "edges": [
                                236238.65625,
                                311515.125,
                                437177.84375,
                                513583.125,
                                684577.1875,
                                1412215.25,
                                None,
                            ],
                            "edge_names": [
                                "left_outlier",
                                "q_20",
                                "q_40",
                                "q_60",
                                "q_80",
                                "q_100",
                                "right_outlier",
                            ],
                            "aggregated_values": [
                                0.0,
                                0.2,
                                0.224,
                                0.18,
                                0.196,
                                0.2,
                                0.0,
                            ],
                            "aggregation": "Density",
                            "start": None,
                            "end": None,
                        }
                    },
                    "window": {
                        "model_name": "house-price-estimator",
                        "path": "output variable 0",
                        "pipeline_name": "assay-demonstration-tutorial-5",
                        "width": "1 minutes",
                        "workspace_id": 2,
                        "interval": "1 minutes",
                        "start": "2024-02-26T02:56:37.290182+00:00",
                        "locations": [],
                    },
                    "summarizer": {
                        "bin_mode": "Quantile",
                        "aggregation": "Density",
                        "metric": "PSI",
                        "num_bins": 5,
                        "type": "UnivariateContinuous",
                        "bin_weights": None,
                        "provided_edges": None,
                    },
                },
            )
        )
        assay_info = self.test_client.get_assay_info(1)
        assert assay_info.iloc[0]["id"] == 1
        assert assay_info.iloc[0]["name"] == "getassayinfotest"
        expected_assay_info = [
            "id",
            "name",
            "active",
            "status",
            "pipeline_name",
            "last_run",
            "next_run",
            "alert_threshold",
            "workspace_id",
            "workspace_name",
            "baseline",
            "iopath",
            "metric",
            "num_bins",
            "bin_weights",
            "bin_mode",
        ]
        assert assay_info.columns.tolist() == expected_assay_info
        assert assay_info.iloc[0]["baseline"] == "Uploaded File"

    @respx.mock()
    def test_get_assay_info_for_assay_built_with_baseline_dates(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/assays/get_assay_by_id",
            json={"id": 1, "workspace_id": None, "workspace_name": None},
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 1,
                    "name": "getassayinfotest",
                    "active": True,
                    "status": '{"run_at": "2024-02-26T03:03:46.393130216+00:00",  "num_ok": 1, "num_warnings": 0, "num_alerts": 1}',
                    "alert_threshold": 0.25,
                    "pipeline_id": 1,
                    "pipeline_name": "assay-demonstration-tutorial-5",
                    "workspace_id": 1,
                    "workspace_name": "test_workspace",
                    "next_run": "2024-02-26T03:03:37.290182+00:00",
                    "warning_threshold": None,
                    "last_run": "2024-02-26T03:03:46.39313+00:00",
                    "run_until": "2024-02-26T03:03:39.507103+00:00",
                    "created_at": "2024-02-26T03:03:46.183491+00:00",
                    "updated_at": "2024-02-26T03:03:46.183491+00:00",
                    "baseline": {
                        "static": {
                            "count": 500,
                            "min": 236238.65625,
                            "max": 1412215.25,
                            "mean": 514178.5481875,
                            "median": 449699.75,
                            "std": 229036.31316679736,
                            "edges": [
                                236238.65625,
                                311515.125,
                                437177.84375,
                                513583.125,
                                684577.1875,
                                1412215.25,
                                None,
                            ],
                            "edge_names": [
                                "left_outlier",
                                "q_20",
                                "q_40",
                                "q_60",
                                "q_80",
                                "q_100",
                                "right_outlier",
                            ],
                            "aggregated_values": [
                                0.0,
                                0.2,
                                0.224,
                                0.18,
                                0.196,
                                0.2,
                                0.0,
                            ],
                            "aggregation": "Density",
                            "start": "2024-02-26T02:56:37.290182+00:00",
                            "end": "2024-02-27T02:56:37.290182+00:00",
                        }
                    },
                    "window": {
                        "model_name": "house-price-estimator",
                        "path": "output variable 0",
                        "pipeline_name": "assay-demonstration-tutorial-5",
                        "width": "1 minutes",
                        "workspace_id": 2,
                        "interval": "1 minutes",
                        "start": "2024-02-26T02:56:37.290182+00:00",
                        "locations": [],
                    },
                    "summarizer": {
                        "bin_mode": "Quantile",
                        "aggregation": "Density",
                        "metric": "PSI",
                        "num_bins": 5,
                        "type": "UnivariateContinuous",
                        "bin_weights": None,
                        "provided_edges": None,
                    },
                },
            )
        )
        assay_info = self.test_client.get_assay_info(1)
        assert assay_info.iloc[0]["id"] == 1
        assert assay_info.iloc[0]["name"] == "getassayinfotest"
        expected_assay_info = [
            "id",
            "name",
            "active",
            "status",
            "pipeline_name",
            "last_run",
            "next_run",
            "alert_threshold",
            "workspace_id",
            "workspace_name",
            "baseline",
            "iopath",
            "metric",
            "num_bins",
            "bin_weights",
            "bin_mode",
        ]
        assert assay_info.columns.tolist() == expected_assay_info
        assert (
            assay_info.iloc[0]["baseline"]
            == "Start:2024-02-26T02:56:37.290182+00:00, End:2024-02-27T02:56:37.290182+00:00"
        )

    @respx.mock(assert_all_mocked=True)
    def test_build_assay(self, respx_mock):
        class Pipeline:
            def id(self):
                return 0

            def name(self):
                return "pipy"

        respx_mock.post(
            "http://api-lb:8080/v1/api/assays/summarize",
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "count": 188,
                    "min": 11.986584663391112,
                    "max": 14.29722023010254,
                    "mean": 13.031112508570894,
                    "median": 12.956134796142578,
                    "std": 0.4770556767131347,
                    "edges": [
                        11.986584663391112,
                        12.622478485107422,
                        12.854415893554688,
                        13.064453125,
                        13.440485000610352,
                        14.29722023010254,
                        None,
                    ],
                    "edge_names": [
                        "left_outlier",
                        "q_20",
                        "q_40",
                        "q_60",
                        "q_80",
                        "q_100",
                        "right_outlier",
                    ],
                    "aggregated_values": [
                        0.0,
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.19680851063829788,
                        0.20212765957446807,
                        0.0,
                    ],
                    "aggregation": "Density",
                    "start": "2023-01-01T00:00:00+00:00",
                    "end": "2023-01-02T00:00:00+00:00",
                },
            )
        )
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)

        gql_client = testutil.new_gql_client(endpoint="http://api-lb:8080/v1/graphql")
        client = wallaroo.Client(
            gql_client=gql_client,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )

        p = Pipeline()
        a = client.build_assay(
            assay_name="test",
            pipeline=cast(wallaroo.pipeline.Pipeline, p),
            iopath="output 0 0",
            model_name="model_name",
            baseline_start=datetime.now(),
            baseline_end=datetime.now(),
        )
        ad = json.loads(a.build().to_json())
        assert ad["name"] == "test"

    @respx.mock(assert_all_mocked=True)
    def test_build_assay_errors_when_positional_args_are_used(self, respx_mock):
        class Pipeline:
            def id(self):
                return 0

        gql_client = testutil.new_gql_client(endpoint="http://api-lb:8080/v1/graphql")
        client = wallaroo.Client(
            gql_client=gql_client,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )

        p = Pipeline()
        # build_assay doesn't accept position arguments
        with pytest.raises(TypeError):
            client.build_assay(
                "test",
                cast(wallaroo.pipeline.Pipeline, p),
                "output 0 0",
                "model_name",
                datetime.now(),
                datetime.now(),
            )

    # Tests for _wait_for_model method
    def _create_mock_status_sequence(self, statuses):
        """Helper to create mock model responses with given status sequence."""
        responses = []
        for status in statuses:
            mock_model = MagicMock()
            mock_model.status.return_value = status
            responses.append(mock_model)
        return responses

    def _run_wait_for_model_test(self, status_sequence, should_raise=None):
        """Helper to run _wait_for_model with mocked dependencies."""
        mock_responses = self._create_mock_status_sequence(status_sequence)
        mock_model_version = MagicMock()

        with (
            patch("wallaroo.client.time.sleep"),
            patch("sys.stdout", new_callable=StringIO) as mock_stdout,
            patch("sys.stderr", new_callable=StringIO) as mock_stderr,
            patch.object(
                self.test_client,
                "_get_configured_model_version",
                side_effect=mock_responses,
            ),
        ):
            if should_raise:
                with pytest.raises(should_raise):
                    self.test_client._wait_for_model(mock_model_version)
                return mock_stdout.getvalue() + mock_stderr.getvalue(), None
            else:
                result = self.test_client._wait_for_model(mock_model_version)
                return mock_stdout.getvalue() + mock_stderr.getvalue(), result

    def test_wait_for_model_successful_native_loading(self):
        """Test successful model loading to native runtime."""
        from wallaroo.wallaroo_ml_ops_api_client.models.model_status import ModelStatus

        output, result = self._run_wait_for_model_test(
            [
                ModelStatus.PENDING_LOAD_NATIVE,
                ModelStatus.ATTEMPTING_LOAD_NATIVE,
                ModelStatus.READY,
            ]
        )

        assert "Waiting for model loading - this will take up to 10min." in output
        assert "Model is pending loading to a native runtime" in output
        assert "Model is attempting loading to a native runtime" in output
        assert "Successful" in output
        assert "Ready" in output
        assert result is not None

    def test_wait_for_model_runtime_fallback(self):
        """Test fallback from native to container runtime."""
        from wallaroo.wallaroo_ml_ops_api_client.models.model_status import ModelStatus

        output, _ = self._run_wait_for_model_test(
            [
                ModelStatus.PENDING_LOAD_NATIVE,
                ModelStatus.ATTEMPTING_LOAD_NATIVE,
                ModelStatus.PENDING_LOAD_CONTAINER,
                ModelStatus.ATTEMPTING_LOAD_CONTAINER,
                ModelStatus.READY,
            ]
        )

        assert "Incompatible" in output  # After native attempt fails
        assert "Successful" in output  # After container succeeds
        assert "Ready" in output

    def test_wait_for_model_error_handling(self):
        """Test error state handling."""
        from wallaroo.wallaroo_ml_ops_api_client.models.model_status import ModelStatus

        # Error handling now returns model with error instead of raising
        output, result = self._run_wait_for_model_test(
            [
                ModelStatus.PENDING_LOAD_NATIVE,
                ModelStatus.ATTEMPTING_LOAD_NATIVE,
                ModelStatus.ERROR,
            ]
        )

        assert "ERROR!" in output
        assert "Incompatible" in output
        # Check for red error message formatting
        assert "\033[91m" in output, "Error message should be printed in red"
        assert "There was an error during model conversion" in output
        assert "upload_logs()" in output
        # Verify model is returned with error stored
        assert result is not None
        assert hasattr(result, "_wait_error")
        assert result._wait_error is not None

    def test_wait_for_model_timeout(self):
        """Test timeout handling."""
        from wallaroo.wallaroo_ml_ops_api_client.models.model_status import ModelStatus

        original_timeout = wallaroo.client.DEFAULT_MODEL_CONVERSION_TIMEOUT
        wallaroo.client.DEFAULT_MODEL_CONVERSION_TIMEOUT = 0.1

        try:
            # Status stays same (will timeout)
            mock_model = MagicMock()
            mock_model.status.return_value = ModelStatus.PENDING_LOAD_NATIVE

            with (
                patch("wallaroo.client.time.sleep"),
                patch("sys.stdout", new_callable=StringIO) as mock_stdout,
                patch("sys.stderr", new_callable=StringIO) as mock_stderr,
                patch.object(
                    self.test_client,
                    "_get_configured_model_version",
                    return_value=mock_model,
                ),
            ):
                # Timeout now returns model with error instead of raising
                result = self.test_client._wait_for_model(MagicMock())

            output = mock_stdout.getvalue() + mock_stderr.getvalue()
            assert "Waiting for model loading - this will take up to 10min." in output
            assert "." in output  # Should have progress dots
            # Check for red timeout error message
            assert (
                "\033[91m" in output
            ), "Timeout error message should be printed in red"
            assert "There was an error during model conversion" in output
            assert "timed out" in output.lower()
            assert "upload_logs()" in output
            # Verify model is returned with timeout error stored
            assert result is not None
            assert hasattr(result, "_wait_error")
            assert result._wait_error is not None
        finally:
            wallaroo.client.DEFAULT_MODEL_CONVERSION_TIMEOUT = original_timeout

    def test_wait_for_model_immediate_ready(self):
        """Test immediate ready state."""
        from wallaroo.wallaroo_ml_ops_api_client.models.model_status import ModelStatus

        output, result = self._run_wait_for_model_test([ModelStatus.READY])

        assert "Waiting for model loading - this will take up to 10min." in output
        assert "Ready" in output
        # Should not have progress dots (only dots in the initial message)
        lines = output.split("\n")
        progress_lines = [line for line in lines if "Model is" in line]
        for line in progress_lines:
            assert not line.endswith(".")  # No progress dots on status lines
        assert result is not None

    def test_wait_for_model_output_integrity(self):
        """Test that output formatting is clean and consistent."""
        from wallaroo.wallaroo_ml_ops_api_client.models.model_status import ModelStatus

        output, _ = self._run_wait_for_model_test(
            [
                ModelStatus.PENDING_LOAD_NATIVE,
                ModelStatus.ATTEMPTING_LOAD_NATIVE,
                ModelStatus.READY,
            ]
        )

        lines = output.split("\n")

        # Verify no text corruption (lines starting with '..')
        corrupted_lines = [line for line in lines if line.startswith("..")]
        assert not corrupted_lines, f"Found corrupted lines: {corrupted_lines}"

        # Verify each message appears exactly once
        assert (
            output.count("Waiting for model loading - this will take up to 10min.") == 1
        )
        assert output.count("Model is pending loading to a native runtime") == 1
        assert output.count("Successful") == 1
        assert output.count("Ready") == 1
