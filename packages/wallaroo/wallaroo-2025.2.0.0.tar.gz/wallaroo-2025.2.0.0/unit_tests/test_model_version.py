import datetime
import time
from io import StringIO
from unittest.mock import patch

import httpx
import pytest
import respx

import wallaroo
from wallaroo.continuous_batching_config import ContinuousBatchingConfig
from wallaroo.deployment import WaitForDeployError, WaitForError
from wallaroo.dynamic_batching_config import DynamicBatchingConfig
from wallaroo.engine_config import Acceleration
from wallaroo.model_version import ModelVersion
from wallaroo.object import InvalidNameError
from wallaroo.pipeline import Pipeline
from wallaroo.tag import Tag

from . import status_samples, testutil
from .reusable_responders import (
    add_create_pipeline_responder,
    add_default_workspace_responder,
    add_deploy_responder,
    add_get_model_config_response,
    add_insert_model_config_response,
    add_undeploy_responder,
)


class TestModelVersion:
    def setup_method(self):
        self.now = datetime.datetime.now()
        self.gql_client = testutil.new_gql_client(endpoint="http://api-lb/v1/graphql")
        self.test_client = wallaroo.Client(
            gql_client=self.gql_client,
            request_timeout=2,
            interactive=False,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )

    def add_deploy_onnx_responses(self, respx_mock):
        add_deploy_responder(respx_mock, 3, self.test_client.api_endpoint)

        respx_mock.post(
            "http://api-lb/v1/graphql",
            content__contains="query {}".format("DeploymentById"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "deployment_by_pk": {
                            "id": 3,
                            "deploy_id": "my-deployment-name",
                            "deployed": False,
                            "deployment_model_configs": [
                                {
                                    "model_config": {
                                        "id": 3,
                                    },
                                },
                            ],
                        },
                    },
                },
            ),
        )

        respx_mock.post(
            "http://api-lb/v1/graphql",
            content__contains="query {}".format("UserDefaultWorkspace"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "user_default_workspace": [
                            {
                                "workspace": {
                                    "id": 1,
                                }
                            }
                        ]
                    }
                },
            ),
        )

        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/status/get_deployment",
            json={"name": "my-deployment-name-3"},
        ).mock(return_value=httpx.Response(200, json=status_samples.RUNNING))

        respx_mock.post(
            "http://api-lb/v1/graphql",
            content__contains="query {}".format("ModelConfigById"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "model_config_by_pk": {
                            "id": 1,
                            "filter_threshold": 0.1234,
                            "model": {
                                "id": 2,
                            },
                            "runtime": "onnx",
                            "tensor_fields": None,
                        },
                    },
                },
            )
        )

        respx_mock.post(
            "http://api-lb/v1/graphql",
            content__contains="query {}".format("ModelById"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "model_by_pk": {
                            "id": 1,
                            "sha": "adfaf",
                            "model_id": "some_model_name",
                            "model_version": "some_model_variant_name",
                            "file_name": "some_model_file.onnx",
                            "updated_at": self.now.isoformat(),
                            "visibility": "private",
                            "arch": None,
                            "accel": Acceleration._None,
                        },
                    },
                },
            )
        )

        add_create_pipeline_responder(
            respx_mock, api_endpoint=self.test_client.api_endpoint
        )

        respx_mock.post(
            "http://api-lb/v1/graphql",
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
            )
        )

        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/status/get_deployment",
            json={"name": "my-deployment-name-3"},
        ).mock(return_value=httpx.Response(200, json=status_samples.RUNNING))

    def create_onnx_model(self, client):
        return ModelVersion(
            client=client,
            data={
                "id": 1,
                "model_id": "some_model_name",
                "model_version": "some_model_variant_name",
                "file_name": "some_model_file.onnx",
                "updated_at": self.now.isoformat(),
                "visibility": "private",
            },
        )

    @respx.mock(assert_all_mocked=True)
    def test_init_full_dict(self):
        variant = ModelVersion(
            client=self.test_client,
            data={
                "id": 1,
                "model_id": "some_model_name",
                "model_version": "some_model_variant_name",
                "file_name": "some_model_file.onnx",
                "updated_at": self.now.isoformat(),
                "visibility": "private",
            },
        )

        assert 1 == variant.id()
        assert "some_model_variant_name" == variant.version()
        assert "some_model_name" == variant.name()
        assert "some_model_file.onnx" == variant.file_name()
        assert self.now == variant.last_update_time()

    @pytest.mark.parametrize(
        "method_name, want_value",
        [
            ("name", "some_model_name"),
            ("version", "some_model_variant_name"),
            ("status", "ready"),
            ("file_name", "some_model_file.onnx"),
            ("last_update_time", datetime.datetime(2024, 1, 1, 0, 0, 0)),
        ],
    )
    @respx.mock(assert_all_mocked=True)
    def test_rehydrate(self, method_name, want_value, respx_mock):
        respx_mock.post(
            "http://api-lb/v1/graphql",
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
                            "updated_at": datetime.datetime(
                                2024, 1, 1, 0, 0, 0
                            ).isoformat(),
                            "visibility": "private",
                            "model": {
                                "workspace": {"id": 1, "name": "test-workspace"},
                            },
                        },
                    },
                },
            )
        )

        variant = ModelVersion(client=self.test_client, data={"id": 1})

        assert want_value == getattr(variant, method_name)()
        if method_name == "status":
            assert 2 == len(respx_mock.calls)
        else:
            assert 1 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=True)
    def test_configure(self, respx_mock):
        add_insert_model_config_response(respx_mock, self.test_client.api_endpoint)
        model = ModelVersion(
            client=self.test_client,
            data={
                "id": 1,
                "model_id": "some_model_name",
                "model_version": "some_model_variant_name",
                "file_name": "some_model_file.onnx",
                "updated_at": self.now.isoformat(),
                "visibility": "private",
            },
        )
        config = model.configure(runtime="onnx")

        assert isinstance(config, ModelVersion)
        assert 1 == len(respx_mock.calls)

    def test_configure_with_batch_config_single_fails_with_dynamic_batching_config_set(
        self,
    ):
        model = ModelVersion(
            client=self.test_client,
            data={
                "id": 1,
                "model_id": "some_model_name",
                "model_version": "some_model_variant_name",
                "file_name": "some_model_file.onnx",
                "updated_at": self.now.isoformat(),
                "visibility": "private",
            },
        )
        dynamic_batching_config = DynamicBatchingConfig(
            max_batch_delay_ms=10, batch_size_target=4, batch_size_limit=10
        )
        with pytest.raises(ValueError):
            model.configure(
                runtime="onnx",
                batch_config="single",
                dynamic_batching_config=dynamic_batching_config,
            )

    def test_configure_with_batch_config_fails_with_continuous_batching_config_set(
        self,
    ):
        model = ModelVersion(
            client=self.test_client,
            data={
                "id": 1,
                "model_id": "some_model_name",
                "model_version": "some_model_variant_name",
                "file_name": "some_model_file.onnx",
                "updated_at": self.now.isoformat(),
                "visibility": "private",
            },
        )
        continuous_batching_config = ContinuousBatchingConfig(
            max_concurrent_batch_size=1
        )

        with pytest.raises(ValueError):
            model.configure(
                batch_config="single",
                continuous_batching_config=continuous_batching_config,
            )

    @respx.mock(assert_all_mocked=False)
    def test_deploy_onnx_noninteractive(self, respx_mock):
        add_default_workspace_responder(respx_mock, "http://api-lb")
        self.add_deploy_onnx_responses(respx_mock)
        add_create_pipeline_responder(
            respx_mock, api_endpoint=self.test_client.api_endpoint
        )
        variant = self.create_onnx_model(self.test_client)
        add_get_model_config_response(respx_mock, self.test_client.api_endpoint)
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            with patch("sys.stderr", new_callable=StringIO) as stderr:
                deployment = variant.deploy("my-deployment-name")
                assert stdout.getvalue() == ""
                assert stderr.getvalue() == ""

        assert isinstance(deployment, Pipeline)

        # tack on a failure case
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/status/get_deployment",
            json={"name": "my-deployment-name-3"},
        ).mock(return_value=httpx.Response(200, json=status_samples.ERROR))

        beg = time.time()
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            with patch("sys.stderr", new_callable=StringIO) as stderr:
                with pytest.raises(WaitForDeployError):
                    deployment = variant.deploy("my-deployment-name")
                assert stdout.getvalue() == ""
                assert stderr.getvalue() == ""

        end = time.time()
        assert end - beg > 2

    @respx.mock(assert_all_mocked=True)
    def test_deploy_onnx_interactive(self, respx_mock):
        test_client = wallaroo.Client(
            gql_client=self.gql_client,
            request_timeout=2,
            interactive=True,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )

        self.add_deploy_onnx_responses(respx_mock)
        variant = self.create_onnx_model(test_client)
        add_get_model_config_response(respx_mock, test_client.api_endpoint)

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            with patch("sys.stderr", new_callable=StringIO) as stderr:
                # validate that 'deploy' requires DNS-compliant names
                try:
                    variant.deploy("not-quite-right-")
                except InvalidNameError as _:
                    pass
                else:
                    assert False
                deployment = variant.deploy("my-deployment-name")
                assert stdout.getvalue() == " ok\n"
                assert stderr.getvalue() == ""

        assert isinstance(deployment, Pipeline)

        # tack on a failure case
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/status/get_deployment",
            json={"name": "my-deployment-name-3"},
        ).mock(return_value=httpx.Response(200, json=status_samples.ERROR))

        beg = time.time()
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            with patch("sys.stderr", new_callable=StringIO) as stderr:
                with pytest.raises(WaitForDeployError):
                    deployment = variant.deploy("my-deployment-name")
                assert stdout.getvalue().startswith("Waiting for deployment")
                assert stderr.getvalue() == ""

        end = time.time()
        assert end - beg > 2

    @respx.mock(assert_all_mocked=True)
    def test_undeploy_onnx_interactive(self, respx_mock):
        test_client = wallaroo.Client(
            gql_client=self.gql_client,
            request_timeout=2,
            interactive=True,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )

        self.add_deploy_onnx_responses(respx_mock)
        add_undeploy_responder(respx_mock, self.test_client.api_endpoint)
        variant = self.create_onnx_model(test_client)
        add_get_model_config_response(respx_mock, test_client.api_endpoint)

        # get a normal deployment
        success_deployment = variant.deploy("my-deployment-name")
        assert isinstance(success_deployment, Pipeline)

        # failure case
        beg = time.time()
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            with patch("sys.stderr", new_callable=StringIO) as stderr:
                with pytest.raises(WaitForError):
                    deployment = success_deployment.undeploy()
                assert stdout.getvalue().startswith("Waiting for undeployment")
                assert stderr.getvalue() == ""

        end = time.time()
        assert end - beg > 2

        # success case
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/status/get_deployment",
            json={"name": "my-deployment-name-3"},
        ).mock(return_value=httpx.Response(404))
        with patch("sys.stdout", new_callable=StringIO) as stdout:
            with patch("sys.stderr", new_callable=StringIO) as stderr:
                success_deployment.undeploy()
                outvalue = stdout.getvalue()
                assert stdout.getvalue() == " ok\n"
                assert stderr.getvalue() == ""

    @respx.mock(assert_all_mocked=True)
    def test_pipeline_tags(self, respx_mock):
        tag_1 = Tag(client=self.test_client, data={"id": 1, "tag": "bartag314"})
        tag_2 = Tag(client=self.test_client, data={"id": 2, "tag": "footag123"})

        respx_mock.post(
            "http://api-lb/v1/graphql",
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
                            "file_name": "some_model_file.onnx",
                            "updated_at": self.now.isoformat(),
                            "visibility": "private",
                            "model_tags": [
                                {"tag": {"id": 1, "tag": "bartag314"}},
                                {"tag": {"id": 2, "tag": "footag123"}},
                            ],
                        },
                    },
                },
            )
        )

        variant = ModelVersion(client=self.test_client, data={"id": 1})
        assert list(map(vars, [tag_1, tag_2])) == list(map(vars, variant.tags()))
