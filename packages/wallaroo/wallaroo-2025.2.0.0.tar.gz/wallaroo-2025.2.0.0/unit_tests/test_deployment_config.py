import json
import os
from datetime import datetime

import httpx
import pytest
import respx

import wallaroo
from wallaroo.deployment_config import DeploymentConfigBuilder
from wallaroo.engine_config import Acceleration, QaicWithConfig
from wallaroo.model_version import ModelVersion

from . import testutil


@pytest.fixture
def gql_client():
    return testutil.new_gql_client(endpoint="http://api-lb:8080/v1/graphql")


@pytest.fixture
def test_client(gql_client):
    return wallaroo.Client(
        gql_client=gql_client,
        auth_type="test_auth",
        api_endpoint="http://api-lb:8080",
        config={"default_arch": "x86"},
    )


@pytest.fixture
def now():
    return datetime.now()


@pytest.fixture
def builder():
    return DeploymentConfigBuilder()


@pytest.fixture
def basic_config():
    """Fixture for a basic deployment configuration."""
    return {
        "image": "fake",
        "replicas": 5,
        "cpus": 0.1,
        "memory": "10MiB",
        "lb_cpus": 0.2,
        "lb_memory": "20MiB",
    }


def test_simple(builder):
    config = builder.build()
    assert config == {
        "engine": {},
        "enginelb": {},
        "engineAux": {"images": {}},
    }


def test_override_image(builder):
    config = builder.image("foo_image").build()
    assert config == {
        "engine": {"image": "foo_image"},
        "enginelb": {},
        "engineAux": {"images": {}},
    }


def test_override_replicas(builder):
    config = builder.replica_count(2).build()

    assert config == {
        "engine": {"replicas": 2},
        "enginelb": {},
        "engineAux": {"images": {}},
    }


def test_override_engine_params(builder):
    config = builder.cpus(3).memory("2Gi").build()

    assert config == {
        "engine": {
            "cpu": 3,
            "resources": {
                "limits": {"cpu": 3, "memory": "2Gi"},
                "requests": {"cpu": 3, "memory": "2Gi"},
            },
        },
        "enginelb": {},
        "engineAux": {"images": {}},
    }


def test_override_lb_params(builder):
    config = builder.lb_cpus(3).lb_memory("2Gi").build()

    assert config == {
        "engine": {},
        "enginelb": {
            "resources": {
                "limits": {
                    "cpu": 3,
                    "memory": "2Gi",
                },
                "requests": {
                    "cpu": 3,
                    "memory": "2Gi",
                },
            }
        },
        "engineAux": {"images": {}},
    }


def test_set_replica_autoscale_min_max(builder):
    serial = json.dumps(
        {
            "image": "fake",
            "replicas": 1,
            "cpus": 0.1,
            "memory": "10MiB",
            "lb_cpus": 0.2,
            "lb_memory": "20MiB",
        }
    )
    os.environ["DEPLOYMENT_CONFIG"] = serial
    dc = DeploymentConfigBuilder()
    dc.replica_autoscale_min_max(minimum=1, maximum=2)
    dc = dc.build()
    assert 1 == dc["engine"]["autoscale"]["replica_min"]
    assert 2 == dc["engine"]["autoscale"]["replica_max"]
    assert "cpu" == dc["engine"]["autoscale"]["type"]
    assert 1 == dc["engine"]["replicas"]
    del os.environ["DEPLOYMENT_CONFIG"]


def test_set_autoscale_cpu_utilization(basic_config, builder):
    os.environ["DEPLOYMENT_CONFIG"] = json.dumps(basic_config.copy())
    dc = builder.autoscale_cpu_utilization(20).build()
    assert 20 == dc["engine"]["autoscale"]["cpu_utilization"]
    del os.environ["DEPLOYMENT_CONFIG"]


def test_set_replica_autoscale_min_max_min_gt_max(basic_config, builder):
    os.environ["DEPLOYMENT_CONFIG"] = json.dumps(basic_config.copy())
    with pytest.raises(
        RuntimeError, match="Minimum must be less than or equal to maximum"
    ):
        builder.replica_autoscale_min_max(minimum=2, maximum=1)
    del os.environ["DEPLOYMENT_CONFIG"]


def test_replica_count_gt_replica_max(basic_config):
    serial = json.dumps(
        {
            "image": "fake",
            "autoscale": {"replica_max": 5},
            "cpus": 0.1,
            "memory": "10MiB",
            "lb_cpus": 0.2,
            "lb_memory": "20MiB",
        }
    )
    os.environ["DEPLOYMENT_CONFIG"] = serial
    dc = DeploymentConfigBuilder()

    with pytest.raises(
        RuntimeError,
        match="Replica count must be less than or equal to replica max. Use replica_autoscale_min_max to adjust this.",
    ):
        dc.replica_count(7)

    del os.environ["DEPLOYMENT_CONFIG"]


def test_env_override():
    serial = json.dumps(
        {
            "image": "fitzroy-mini",
            "replicas": 5,
            "cpus": 0.1,
            "gpus": 0,
            "memory": "10MiB",
            "lb_cpus": 0.2,
            "lb_memory": "20MiB",
        }
    )
    os.environ["DEPLOYMENT_CONFIG"] = serial

    assert DeploymentConfigBuilder().build() == {
        "engine": {
            "image": "fitzroy-mini",
            "replicas": 5,
            "cpu": 0.1,
            "resources": {
                "limits": {"cpu": 0.1, "nvidia.com/gpu": 0, "memory": "10MiB"},
                "requests": {"cpu": 0.1, "nvidia.com/gpu": 0, "memory": "10MiB"},
            },
            "gpu": 0,
        },
        "enginelb": {
            "resources": {
                "limits": {
                    "cpu": 0.2,
                    "memory": "20MiB",
                },
                "requests": {
                    "cpu": 0.2,
                    "memory": "20MiB",
                },
            }
        },
        "engineAux": {"images": {}},
    }

    del os.environ["DEPLOYMENT_CONFIG"]


@respx.mock(assert_all_mocked=False)
def test_sidekick_options(test_client, now, respx_mock):
    barnacle_boy_data = {
        "data": {
            "model_by_pk": {
                "id": 1,
                "sha": "somethingsomething",
                "model_id": "barnacle-boy",
                "model_version": "123abc-456def",
                "image_path": "ghcr.io/wallaroolabs/sidekick-example:1234qwer",
                "updated_at": now.isoformat(),
                "visibility": "private",
            },
        },
    }
    patrick_star_data = {
        "data": {
            "model_by_pk": {
                "id": 1,
                "sha": "somethingsomething",
                "model_id": "patrick-star",
                "model_version": "123abc-456def",
                "image_path": "ghcr.io/wallaroolabs/sidekick-example:1234qwer",
                "updated_at": now.isoformat(),
                "visibility": "private",
            },
        },
    }

    respx_mock.post(
        "http://api-lb:8080/v1/graphql",
        content__contains="model_by_pk(id: 1)",
    ).mock(
        return_value=httpx.Response(
            200,
            json=barnacle_boy_data,
        ),
    )
    respx_mock.post(
        "http://api-lb:8080/v1/graphql",
    ).mock(
        return_value=httpx.Response(
            200,
            json=patrick_star_data,
        ),
    )

    barnacle_boy = ModelVersion(test_client, data={"id": 1})
    patrick_star = ModelVersion(test_client, data={"id": 2})

    config = (
        DeploymentConfigBuilder()
        .sidekick_cpus(barnacle_boy, 1.75)
        .sidekick_memory(barnacle_boy, "1Gi")
        .sidekick_env(barnacle_boy, {"GUNICORN_CMD_ARGS": "-timeout=120 --workers=4"})
        .sidekick_cpus(patrick_star, 0.25)
        .sidekick_memory(patrick_star, "3Gi")
        .sidekick_env(patrick_star, {"GUNICORN_CMD_ARGS": "-timeout=240 --workers=1"})
        .build()
    )
    assert len(config["engineAux"]["images"]) == 2

    assert config["engineAux"]["images"]["barnacle-boy-1"] == {
        "resources": {
            "limits": {
                "cpu": 1.75,
                "memory": "1Gi",
            },
            "requests": {
                "cpu": 1.75,
                "memory": "1Gi",
            },
        },
        "env": [{"name": "GUNICORN_CMD_ARGS", "value": "-timeout=120 --workers=4"}],
    }

    assert config["engineAux"]["images"]["patrick-star-1"] == {
        "resources": {
            "limits": {
                "cpu": 0.25,
                "memory": "3Gi",
            },
            "requests": {
                "cpu": 0.25,
                "memory": "3Gi",
            },
        },
        "env": [{"name": "GUNICORN_CMD_ARGS", "value": "-timeout=240 --workers=1"}],
    }


def test_workspace_injection():
    config = DeploymentConfigBuilder(workspace_id=1).build()

    assert config == {
        "engine": {},
        "enginelb": {},
        "engineAux": {"images": {}},
        "workspace_id": 1,
    }


def test_scale_up_queue_depth_sets_correct_values():
    builder = DeploymentConfigBuilder()
    result = builder.scale_up_queue_depth(5).build()

    assert result["engine"]["autoscale"]["scale_up_queue_depth"] == 5
    assert result["engine"]["autoscale"]["type"] == "queue"


def test_scale_up_queue_depth_sets_default_scale_down():
    builder = DeploymentConfigBuilder()
    deploy_config = builder.scale_up_queue_depth(10).build()

    assert deploy_config["engine"]["autoscale"]["scale_down_queue_depth"] == 1


def test_scale_up_queue_depth_doesnt_override_existing_scale_down(builder):
    deploy_config = builder.scale_up_queue_depth(10).scale_down_queue_depth(3).build()

    assert deploy_config["engine"]["autoscale"]["scale_up_queue_depth"] == 10
    assert deploy_config["engine"]["autoscale"]["scale_down_queue_depth"] == 3

    builder.scale_up_queue_depth(7)
    assert builder._config["engine"]["autoscale"]["scale_up_queue_depth"] == 7
    assert builder._config["engine"]["autoscale"]["scale_down_queue_depth"] == 3


def test_scale_down_queue_depth(builder):
    # Test setting scale_down_queue_depth without scale_up_queue_depth
    with pytest.raises(
        ValueError,
        match="scale_down_queue_depth is only applicable when scale_up_queue_depth is configured",
    ):
        builder.scale_down_queue_depth(2)

    # Test setting scale_down_queue_depth after scale_up_queue_depth
    builder.scale_up_queue_depth(5)
    builder.scale_down_queue_depth(2)
    config = builder.build()

    assert config["engine"]["autoscale"]["scale_up_queue_depth"] == 5
    assert config["engine"]["autoscale"]["scale_down_queue_depth"] == 2

    # Test default value when not specified
    builder = DeploymentConfigBuilder()
    builder.scale_up_queue_depth(5)
    config = builder.build()

    assert config["engine"]["autoscale"]["scale_down_queue_depth"] == 1


def test_autoscaling_window(builder):
    builder.scale_up_queue_depth(10)  # Set up prerequisite
    result = builder.autoscaling_window().build()
    assert result["engine"]["autoscale"]["autoscaling_window"] == 300
    # does overwrite work?
    result = builder.autoscaling_window(600).build()
    assert result["engine"]["autoscale"]["autoscaling_window"] == 600


def test_autoscaling_window_without_scale_up_queue_depth(builder):
    with pytest.raises(
        ValueError,
        match="autoscaling_window is only applicable when scale_up_queue_depth is configured",
    ):
        builder.autoscaling_window(500)


def test_engine_deployment_label(builder):
    builder.deployment_label("wallaroo.ai/acceleration: boom")
    config = builder.build()
    assert config["engine"]["node_selector"] == "wallaroo.ai/acceleration: boom"


@respx.mock(assert_all_mocked=False)
def test_sidekick_deployment_label(test_client, now, respx_mock):
    barnacle_boy_data = {
        "data": {
            "model_by_pk": {
                "id": 1,
                "sha": "somethingsomething",
                "model_id": "barnacle-boy",
                "model_version": "123abc-456def",
                "image_path": "ghcr.io/wallaroolabs/sidekick-example:1234qwer",
                "updated_at": now.isoformat(),
                "visibility": "private",
            },
        },
    }
    patrick_star_data = {
        "data": {
            "model_by_pk": {
                "id": 1,
                "sha": "somethingsomething",
                "model_id": "patrick-star",
                "model_version": "123abc-456def",
                "image_path": "ghcr.io/wallaroolabs/sidekick-example:1234qwer",
                "updated_at": now.isoformat(),
                "visibility": "private",
            },
        },
    }
    respx_mock.post(
        "http://api-lb:8080/v1/graphql",
        content__contains="model_by_pk(id: 1)",
    ).mock(
        return_value=httpx.Response(
            200,
            json=barnacle_boy_data,
        ),
    )
    respx_mock.post(
        "http://api-lb:8080/v1/graphql",
        content__contains="model_by_pk(id: 2)",
    ).mock(
        return_value=httpx.Response(
            200,
            json=patrick_star_data,
        ),
    )

    barnacle_boy = ModelVersion(test_client, data={"id": 1})
    patrick_star = ModelVersion(test_client, data={"id": 2})

    config = (
        DeploymentConfigBuilder()
        .sidekick_cpus(barnacle_boy, 1.75)
        .sidekick_memory(barnacle_boy, "1Gi")
        .sidekick_env(barnacle_boy, {"GUNICORN_CMD_ARGS": "-timeout=120 --workers=4"})
        .sidekick_cpus(patrick_star, 0.25)
        .sidekick_memory(patrick_star, "3Gi")
        .sidekick_env(patrick_star, {"GUNICORN_CMD_ARGS": "-timeout=240 --workers=1"})
        .deployment_label("wallaroo.ai/acceleration: magnum")
        .build()
    )

    assert config["engine"]["node_selector"] == "wallaroo.ai/acceleration: magnum"

    assert len(config["engineAux"]["images"]) == 2

    assert config["engineAux"]["images"]["barnacle-boy-1"] == {
        "resources": {
            "limits": {
                "cpu": 1.75,
                "memory": "1Gi",
            },
            "requests": {
                "cpu": 1.75,
                "memory": "1Gi",
            },
        },
        "env": [{"name": "GUNICORN_CMD_ARGS", "value": "-timeout=120 --workers=4"}],
        "node_selector": "wallaroo.ai/acceleration: magnum",
    }

    assert config["engineAux"]["images"]["patrick-star-1"] == {
        "resources": {
            "limits": {
                "cpu": 0.25,
                "memory": "3Gi",
            },
            "requests": {
                "cpu": 0.25,
                "memory": "3Gi",
            },
        },
        "env": [{"name": "GUNICORN_CMD_ARGS", "value": "-timeout=240 --workers=1"}],
        "node_selector": "wallaroo.ai/acceleration: magnum",
    }


@pytest.mark.parametrize(
    "new_accel, expected_gpu_resource",
    [
        (Acceleration.CUDA, "nvidia.com/gpu"),
        (Acceleration.QAIC, "qualcomm.com/qaic"),
        (Acceleration.OpenVINO, "gpu.intel.com/i915"),
    ],
)
def test_engine_acceleration(builder, new_accel, expected_gpu_resource):
    config = builder.gpus(1).accel(new_accel).build()

    assert config["engine"]["accel"] == str(new_accel)
    assert config["engine"]["resources"]["limits"][expected_gpu_resource] == 1
    assert config["engine"]["resources"]["requests"][expected_gpu_resource] == 1

    gpu_resources = ("nvidia.com/gpu", "qualcomm.com/qaic", "gpu.intel.com/i915")
    for resource in gpu_resources:
        if resource != expected_gpu_resource:
            assert resource not in config["engine"]["resources"]["limits"]
            assert resource not in config["engine"]["resources"]["requests"]


@pytest.mark.parametrize(
    "new_accel, expected_gpu_resource",
    [
        (Acceleration.CUDA, "nvidia.com/gpu"),
        (Acceleration.QAIC, "qualcomm.com/qaic"),
        (Acceleration.OpenVINO, "gpu.intel.com/i915"),
    ],
)
@respx.mock(assert_all_mocked=False)
def test_sidekick_acceleration(
    test_client, now, new_accel, expected_gpu_resource, respx_mock
):
    model_data = {
        "data": {
            "model_by_pk": {
                "id": 1,
                "sha": "some-sha",
                "model_id": "some-model",
                "model_version": "some-version",
                "image_path": "ghcr.io/wallaroolabs/mac-deploy",
                "updated_at": now.isoformat(),
                "visibility": "private",
                "accel": new_accel,
            },
        },
    }

    respx_mock.post(
        "http://api-lb:8080/v1/graphql",
        content__contains="model_by_pk(id: 1)",
    ).mock(
        return_value=httpx.Response(
            200,
            json=model_data,
        ),
    )

    model = ModelVersion(test_client, data={"id": 1})

    config = (
        DeploymentConfigBuilder()
        .sidekick_accel(model, new_accel)
        .sidekick_gpus(model, 1)
        .build()
    )

    model_uid = "some-model-1"
    sidekick_config = config["engineAux"]["images"][model_uid]

    assert model_uid in config["engineAux"]["images"]
    assert sidekick_config["accel"] == str(new_accel)
    assert sidekick_config["resources"]["limits"][expected_gpu_resource] == 1
    assert sidekick_config["resources"]["requests"][expected_gpu_resource] == 1

    gpu_resources = ("nvidia.com/gpu", "qualcomm.com/qaic", "gpu.intel.com/i915")
    for resource in gpu_resources:
        if resource != expected_gpu_resource:
            assert resource not in sidekick_config["resources"]["limits"]
            assert resource not in sidekick_config["resources"]["requests"]


def test_convert_acceleration_dict_to_qaic():
    accel_dict = {
        "qaic": {
            "num_cores": 1,
            "num_devices": 1,
            "ctx_len": 1,
            "prefill_seq_len": 1,
        }
    }
    accel = DeploymentConfigBuilder.convert_acceleration_dict_to_qaic(accel_dict)
    assert isinstance(accel, QaicWithConfig)
    assert accel.config.num_cores == 1
    assert accel.config.num_devices == 1
    assert accel.config.ctx_len == 1
    assert accel.config.prefill_seq_len == 1


@pytest.mark.parametrize(
    "accel",
    [
        json.dumps(
            {
                "qaic": {
                    "num_cores": 1,
                    "num_devices": 1,
                    "ctx_len": 1,
                    "prefill_seq_len": 1,
                }
            }
        ).replace("'", '"'),
        {
            "qaic": {
                "num_cores": 1,
                "num_devices": 1,
                "ctx_len": 1,
                "prefill_seq_len": 1,
            }
        },
    ],
)
def test_convert_acceleration(accel):
    accel = DeploymentConfigBuilder.convert_acceleration(accel)
    assert isinstance(accel, QaicWithConfig)
    assert accel.config.num_cores == 1
    assert accel.config.num_devices == 1
    assert accel.config.ctx_len == 1
    assert accel.config.prefill_seq_len == 1
