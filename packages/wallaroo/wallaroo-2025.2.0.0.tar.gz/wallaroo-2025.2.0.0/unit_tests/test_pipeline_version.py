import datetime
from io import StringIO
from unittest import mock

import pytest
import respx

import wallaroo
from unit_tests.reusable_responders import (
    add_deploy_responder,
    add_deploy_test_responders,
    add_deployment_status_responder,
    add_get_model_by_id_responder,
    add_pipeline_variant_by_id_responder,
)
from wallaroo.deployment import WaitForDeployError
from wallaroo.deployment_config import DeploymentConfigBuilder
from wallaroo.engine_config import (
    Acceleration,
    Architecture,
    InvalidAccelerationError,
    QaicConfig,
)
from wallaroo.model_config import ModelConfig
from wallaroo.model_version import ModelVersion
from wallaroo.pipeline import Pipeline
from wallaroo.pipeline_version import PipelineVersion

from . import status_samples, testutil


class TestPipelineVersion:
    def setup_method(self):
        self.now = datetime.datetime.now()
        self.gql_client = testutil.new_gql_client(
            endpoint="http://api-lb:8080/v1/graphql"
        )
        self.test_client = wallaroo.Client(
            request_timeout=2,
            gql_client=self.gql_client,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )

        self.default_model_config = ModelConfig(
            self.test_client,
            data={
                "id": 1,
                "model": {"id": 1, "model_id": "ccfraud", "model_version": "default"},
            },
        )
        self.experiment_model_config = ModelConfig(
            self.test_client,
            data={
                "id": 2,
                "model": {
                    "id": 2,
                    "model_id": "ccfraud",
                    "model_version": "experiment",
                },
            },
        )
        self.variant = PipelineVersion(
            client=self.test_client,
            data={
                "id": 1,
            },
        )

    def test_init_full_dict(self):
        variant = PipelineVersion(
            client=self.test_client,
            data={
                "id": 2,
                "version": "v1",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat(),
                "definition": {
                    "id": "test-pipeline",
                    "steps": [
                        {
                            "id": "metavalue_split",
                            "args": ["card_type", "default", "gold", "experiment"],
                            "operation": "map",
                        }
                    ],
                },
                "pipeline": {"id": 1},
                "deployment_pipeline_versions": [],
            },
        )

        assert 2 == variant.id()
        assert "v1" == variant.name()
        assert self.now == variant.create_time()
        assert self.now == variant.last_update_time()
        assert {
            "id": "test-pipeline",
            "steps": [
                {
                    "id": "metavalue_split",
                    "args": ["card_type", "default", "gold", "experiment"],
                    "operation": "map",
                }
            ],
        } == variant.definition()
        assert isinstance(variant.pipeline(), Pipeline)
        # TODO: Test deployment_pipeline_versions

    @pytest.mark.parametrize(
        "method_name, want_value",
        [
            ("name", "v1"),
            (
                "create_time",
                datetime.datetime(2024, 1, 1, 0, 0, 0),
            ),  # TODO Find better ways to handle datetimes
            ("last_update_time", datetime.datetime(2024, 2, 1, 0, 0, 0)),
            (
                "definition",
                {
                    "id": "test-pipeline",
                    "steps": [
                        {
                            "id": "metavalue_split",
                            "args": ["card_type", "default", "gold", "experiment"],
                            "operation": "map",
                        }
                    ],
                },
            ),
        ],
    )
    @respx.mock(assert_all_mocked=False)
    def test_rehydrate(self, method_name, want_value, respx_mock):
        add_pipeline_variant_by_id_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            pipeline_id="test-pipeline",
        )

        variant = PipelineVersion(client=self.test_client, data={"id": 2})

        assert want_value == getattr(variant, method_name)()
        assert 1 == len(respx_mock.calls)
        # Another call to the same accessor shouldn't trigger any
        # additional GraphQL queries.
        assert want_value == getattr(variant, method_name)()
        assert 1 == len(respx_mock.calls)

    @respx.mock(assert_all_mocked=False)
    def test_deploy_success(self, respx_mock):
        add_deploy_test_responders(
            respsx_mock=respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            workspace_name="test-logs-workspace",
            pipeline_name="foo-deployment",
        )
        add_deployment_status_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            deployment_name="foo-deployment-10",
            status=status_samples.RUNNING,
        )

        # default workflow
        deployment = self.variant.deploy(
            "foo-deployment", [self.default_model_config, self.experiment_model_config]
        )

        assert 10 == deployment.id()
        assert "foo-deployment" == deployment.name()
        assert "Running" == deployment.status()["status"]

    @respx.mock(assert_all_mocked=False)
    def test_deploy_do_not_wait_for_success(self, respx_mock):
        add_deploy_test_responders(
            respsx_mock=respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            workspace_name="test-logs-workspace",
            pipeline_name="foo-deployment",
        )
        add_deployment_status_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            deployment_name="foo-deployment-10",
            status=status_samples.STARTING,
        )
        # add_deploy_responder(respx_mock, 10, self.test_client.api_endpoint)
        # With wait_for_status=False
        expected_string = (
            "Deployment initiated for foo-deployment. Please check pipeline status.\n"
        )
        with mock.patch("sys.stdout", new=StringIO()) as fake_out:
            deployment = self.variant.deploy(
                "foo-deployment", [self.default_model_config], wait_for_status=False
            )
            assert deployment.id() == 10
            assert fake_out.getvalue() == expected_string
            assert "Starting" == deployment.status()["status"]

    @respx.mock(assert_all_mocked=False)
    def test_deploy_failure(self, respx_mock):
        add_deploy_test_responders(
            respsx_mock=respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            workspace_name="test-logs-workspace",
            pipeline_name="foo-deployment",
        )
        add_deploy_responder(respx_mock, 10, self.test_client.api_endpoint)
        # Test Failure case
        add_deployment_status_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            deployment_name="foo-deployment-10",
            status=status_samples.ERROR,
        )
        with pytest.raises(WaitForDeployError):
            deployment = self.variant.deploy(
                "foo-deployment",
                [self.default_model_config, self.experiment_model_config],
            )

    def test_validate_acceleration_empty(self):
        dc = DeploymentConfigBuilder().build()
        new_dc = PipelineVersion._validate_deployment_config(dc, [])
        assert dc == new_dc

    def test_validate_acceleration_ok(self):
        dc = (
            DeploymentConfigBuilder()
            .arch(Architecture.ARM)
            .accel(Acceleration.CUDA)
            .build()
        )
        new_dc = PipelineVersion._validate_deployment_config(dc, [])
        assert dc == new_dc

    @respx.mock(assert_all_mocked=False)
    def test_validate_acceleration_aux_ok(self, respx_mock):
        add_get_model_by_id_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            arch=Architecture.ARM,
            accel=Acceleration.CUDA,
        )
        mv = ModelVersion(
            self.test_client,
            {
                "id": 1,
                "name": "test-model",
                "arch": str(Architecture.ARM),
                "accel": str(Acceleration.CUDA),
            },
        )
        dc = (
            DeploymentConfigBuilder()
            .sidekick_arch(mv, Architecture.ARM)
            .sidekick_accel(mv, Acceleration.CUDA)
            .build()
        )
        mc = ModelConfig(None, {"id": "test", "model": mv})
        new_dc = PipelineVersion._validate_deployment_config(dc, [mc])
        assert str(Architecture.ARM) == new_dc["engine"].get("arch")
        assert str(Acceleration.CUDA) == new_dc["engine"].get("accel")

    def test_validate_acceleration_err(self):
        dc = DeploymentConfigBuilder().accel(Acceleration.Jetson).build()
        with pytest.raises(InvalidAccelerationError):
            PipelineVersion._validate_deployment_config(dc, [])

    @respx.mock(assert_all_mocked=False)
    def test_validate_acceleration_with_config(self, respx_mock):
        add_get_model_by_id_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            accel=Acceleration.QAIC.with_config(QaicConfig())._parse_to_openapi(),
        )
        mv = ModelVersion(
            self.test_client,
            {
                "id": 1,
                "name": "test-model",
                "arch": str(Architecture.X86),
                "accel": Acceleration.QAIC.with_config(
                    QaicConfig()
                )._parse_to_openapi(),
            },
        )
        dc = DeploymentConfigBuilder().sidekick_gpus(mv, 1).build()
        mc = ModelConfig(None, {"id": "test", "model": mv})
        new_dc = PipelineVersion._validate_deployment_config(dc, [mc])

        expected_qaic_config = {
            "qaic": {
                "num_cores": 16,
                "num_devices": 1,
                "ctx_len": 128,
                "prefill_seq_len": 32,
                "full_batch_size": 8,
                "mxfp6_matmul": False,
                "mxint8_kv_cache": False,
                "aic_enable_depth_first": False,
            }
        }

        assert expected_qaic_config == new_dc["engine"].get("accel")
        assert expected_qaic_config == new_dc["engineAux"]["images"][
            "test-model-1"
        ].get("accel")

    @respx.mock(assert_all_mocked=False)
    def test_validate_acceleration_aux_err(self, respx_mock):
        add_get_model_by_id_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            accel=Acceleration.Jetson,
        )
        mv = ModelVersion(
            self.test_client,
            {
                "id": "test",
                "name": "test",
                "arch": None,
                "accel": str(Acceleration.Jetson),
            },
        )
        dc = DeploymentConfigBuilder().sidekick_accel(mv, Acceleration.Jetson).build()
        mc = ModelConfig(None, {"id": "test", "model": mv})
        with pytest.raises(InvalidAccelerationError):
            PipelineVersion._validate_deployment_config(dc, [mc])
