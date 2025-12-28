# This is a centralized file for reusable httpx and responses mocks
# that may be used across multiple tests. i.e. many tests require a workspace, so
# they all need to be able to respond to a query for one.
from datetime import datetime

import httpx

from unit_tests import status_samples
from wallaroo.engine_config import Acceleration


def add_default_workspace_responder(
    respx_mock, api_endpoint="http://api-lb:8080", workspace_name="345fr"
):
    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
        content__contains="query {}".format("UserDefaultWorkspace"),
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
                                "name": workspace_name,
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


def add_create_pipeline_responder(
    respx_mock,
    pipeline_pk_id=1,
    pipeline_variant_pk_id=1,
    api_endpoint="http://api-lb:8080",
    pipeline_variant_version=1,
):
    respx_mock.post(f"{api_endpoint}/v1/api/pipelines/create").mock(
        return_value=httpx.Response(
            200,
            json={
                "pipeline_pk_id": pipeline_pk_id,
                "pipeline_variant_pk_id": pipeline_variant_pk_id,
                "pipeline_variant_version": pipeline_variant_version,
            },
        )
    )


def add_get_pipeline_by_id_responder(
    respx_mock, api_endpoint="http://api-lb:8080", pipeline_id="test-pipeline"
):
    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
        content__contains="query {}".format("PipelineById"),
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "pipeline_by_pk": {
                        "id": 1,
                        "pipeline_id": pipeline_id,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                        "pipeline_versions": [{"id": 1}],
                        "visibility": "pUbLIC",
                        "pipeline_tags": [
                            {"tag": {"id": 1, "tag": "bartag314"}},
                            {"tag": {"id": 2, "tag": "footag123"}},
                        ],
                    }
                }
            },
        )
    )


def add_pipeline_variant_by_id_responder(
    respx_mock,
    api_endpoint="http://api-lb:8080",
    pipeline_id="test-pipeline",
    created_at=None,
    updated_at=None,
):
    if created_at is None:
        created_at = datetime(2024, 1, 1, 0, 0, 0).isoformat()
    if updated_at is None:
        updated_at = datetime(2024, 2, 1, 0, 0, 0).isoformat()

    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
        content__contains="query {}".format("PipelineVariantById"),
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "pipeline_version_by_pk": {
                        "id": 2,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "version": "v1",
                        "definition": {
                            "id": pipeline_id,
                            "steps": [
                                {
                                    "id": "metavalue_split",
                                    "args": [
                                        "card_type",
                                        "default",
                                        "gold",
                                        "experiment",
                                    ],
                                    "operation": "map",
                                }
                            ],
                        },
                        "pipeline": {"id": 1},
                        "deployment_pipeline_versions": [],
                    }
                }
            },
        ),
    )


def add_deploy_responder(
    respx_mock, expected_deployment_id=1, api_endpoint="http://api-lb:8080"
):
    respx_mock.post(f"{api_endpoint}/v1/api/pipelines/deploy").mock(
        return_value=httpx.Response(200, json={"id": expected_deployment_id})
    )


def add_deployment_status_responder(
    respx_mock,
    api_endpoint="http://api-lb:8080",
    deployment_name="test_deployment",
    status=status_samples.RUNNING,
):
    respx_mock.post(
        f"{api_endpoint}/v1/api/status/get_deployment",
        json={"name": deployment_name},
    ).mock(
        return_value=httpx.Response(200, json=status),
    )


def add_deployment_status_requests_responder(
    respx_mock, api_endpoint="http://api-lb:8080"
):
    respx_mock.post(f"{api_endpoint}/v1/api/status").mock(
        return_value=httpx.Response(200, json={})
    )


def add_undeploy_responder(respx_mock, api_endpoint="http://api-lb:8080"):
    respx_mock.post(f"{api_endpoint}/v1/api/pipelines/undeploy").mock(
        return_value=httpx.Response(200, json={})
    )


def add_deployment_by_id_responder(
    respx_mock,
    api_endpoint="http://api-lb:8080",
    deployment_id=1,
    deployment_name="some-pipeline",
    deployed=True,
):
    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
        content__contains="query {}".format("DeploymentById"),
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "deployment_by_pk": {
                        "id": deployment_id,
                        "deploy_id": deployment_name,
                        "deployed": deployed,
                        "pipeline": {
                            "pipeline_id": deployment_name,
                        },
                    },
                },
            },
        ),
    )


def add_insert_model_config_response(respx_mock, api_endpoint="http://api-lb:8080"):
    respx_mock.post(f"{api_endpoint}/v1/api/models/insert_model_config").mock(
        return_value=httpx.Response(
            200,
            json={
                "model_config": {
                    "id": 1,
                    "model_version_id": 1,
                    "runtime": "mlflow",
                    "input_schema": "/////Base64EncodedInputSchema=",
                    "output_schema": "/////Base64EncodedOutputSchema=",
                },
            },
        ),
    )


def add_insert_model_config_response_with_config(
    respx_mock, api_endpoint="http://api-lb:8080", gen_id=1, model_config={}
):
    respx_mock.post(f"{api_endpoint}/v1/api/models/insert_model_config").mock(
        return_value=httpx.Response(
            200,
            json={
                "model_config": {
                    "id": gen_id,
                    "tensor_fields": None,
                    "filter_threshold": None,
                    "dynamic_batching_config": None,
                    **model_config,
                }
            },
        )
    )


def add_get_model_config_by_id_responder(respx_mock, api_endpoint="http://api-lb:8080"):
    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
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
                            "id": 1,
                        },
                        "runtime": "onnx",
                        "tensor_fields": None,
                    },
                },
            },
        )
    )


def add_get_model_by_id_responder(
    respx_mock,
    api_endpoint="http://api-lb:8080",
    model_id=1,
    arch=None,
    accel=Acceleration._None,
):
    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
        content__contains="query {}".format("ModelById"),
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "model_by_pk": {
                        "id": model_id,
                        "sha": "adsfadsf",
                        "model_id": "test-model",
                        "model_version": "v2",
                        "status": "ready",
                        "file_name": "some_model_file.onnx",
                        "updated_at": datetime.now().isoformat(),
                        "visibility": "private",
                        "arch": arch,
                        "accel": accel,
                        "model": {
                            "workspace": {"id": 1, "name": "test-workspace"},
                        },
                    },
                },
            },
        )
    )


def add_get_model_config_response(respx_mock, api_endpoint="http://api-lb:8080"):
    respx_mock.post(f"{api_endpoint}/v1/api/models/get_config_by_id").mock(
        return_value=httpx.Response(
            200,
            json={
                "model_config": {
                    "id": 1,
                    "model_version_id": 1,
                    "runtime": "mlflow",
                    "input_schema": "/////Base64EncodedInputSchema=",
                    "output_schema": "/////Base64EncodedOutputSchema=",
                },
            },
        )
    )


def add_get_topic_name_responder(respx_mock, api_endpoint="http://api-lb:8080"):
    respx_mock.post(
        f"{api_endpoint}/v1/api/plateau/get_topic_name",
        json={"pipeline_pk_id": 1},
    ).mock(
        return_value=httpx.Response(
            200,
            json={"topic_name": "workspace-1-pipeline-x-inference"},
        ),
    )


def get_assay_by_id_responder(respx_mock, api_endpoint="http://api-lb:8080"):
    respx_mock.post(
        f"{api_endpoint}/v1/api/assays/get_assay_by_id",
        json={"id": 27, "workspace_id": None, "workspace_name": None},
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
                        "aggregated_values": [0.0, 0.2, 0.224, 0.18, 0.196, 0.2, 0.0],
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
        ),
    )


def add_get_workspace_by_id_responder(
    respx_mock, api_endpoint="http://api-lb:8080", workspace_id=1
):
    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
        content__contains="query {}".format("WorkspaceById"),
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "workspace_by_pk": {
                        "id": workspace_id,
                        "name": f"test-workspace-{workspace_id}",
                        "created_at": datetime.now().isoformat(),
                        "created_by": 44,
                        "pipelines": [{"id": 1}],
                        "models": [{"id": 1}, {"id": 2}],
                        "users": [{"user_id": "UUID-3"}, {"user_id": "UUID-4"}],
                        "archived": False,
                    }
                },
            },
        )
    )


def add_pipeline_by_id_responder(
    respx_mock, api_endpoint="http://api-lb:8080", pipeline_id=1
):
    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
        content__contains="query {}".format("PipelineById"),
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "pipeline_by_pk": {
                        "id": pipeline_id,
                        "pipeline_id": f"pipeline-{pipeline_id}",
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
                            "id": pipeline_id,
                            "name": f"test - default workspace {pipeline_id}",
                        },
                    }
                }
            },
        )
    )


def add_list_models_responder(respx_mock, api_endpoint, request_dict, response_dict):
    respx_mock.post(f"{api_endpoint}/v1/api/models/list", json=request_dict).mock(
        return_value=httpx.Response(200, json=response_dict)
    )


def add_deploy_test_responders(
    respsx_mock,
    api_endpoint="http://api-lb:8080",
    workspace_name="test-logs-workspace",
    pipeline_name="foo-deployment",
):
    add_default_workspace_responder(
        respsx_mock, api_endpoint=api_endpoint, workspace_name=workspace_name
    )

    # ids will be wrong for one of the model config calls, but we're only checking runtime
    add_get_model_config_by_id_responder(respsx_mock, api_endpoint=api_endpoint)
    add_deployment_by_id_responder(
        respsx_mock,
        api_endpoint=api_endpoint,
        deployment_id=10,
        deployment_name=pipeline_name,
    )
    add_get_model_by_id_responder(respsx_mock, api_endpoint=api_endpoint, model_id=1)
    add_deploy_responder(
        respx_mock=respsx_mock, expected_deployment_id=10, api_endpoint=api_endpoint
    )


def add_tag_by_id_responder(respx_mock, api_endpoint="http://api-lb:8080"):
    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
        content__contains="query {}".format("TagById"),
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "tag_by_pk": {
                        "id": 1,
                        "tag": "Great new tag",
                        "model_tags": [
                            {
                                "model": {
                                    "id": 1,
                                    "model_id": "ccfraudmodel",
                                    "models_pk_id": 1,
                                    "model_version": "efb618e5-ba1a-4e05-9c3a-49dd1a053bfc",
                                }
                            }
                        ],
                        "pipeline_tags": [
                            {
                                "pipeline": {
                                    "id": 1,
                                    "pipeline_id": "ccfraudmodel",
                                    "pipeline_versions": [
                                        {
                                            "id": 1,
                                            "version": "ad892ca6-62b3-4ff9-8bb5-347eb851bd48",
                                        },
                                        {
                                            "id": 2,
                                            "version": "612c163b-92e1-4ee3-a542-d84c8704a3e9",
                                        },
                                    ],
                                }
                            }
                        ],
                    }
                }
            },
        )
    )


def add_list_tags_responder(respx_mock, api_endpoint="http://api-lb:8080"):
    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
        content__contains="query {}".format("ListTags"),
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "tag": [
                        {
                            "id": 1,
                            "tag": "Great new tag",
                            "model_tags": [
                                {
                                    "model": {
                                        "id": 1,
                                        "model_id": "ccfraudmodel",
                                        "models_pk_id": 1,
                                        "model_version": "efb618e5-ba1a-4e05-9c3a-49dd1a053bfc",
                                    }
                                }
                            ],
                        }
                    ]
                }
            },
        )
    )


def add_get_configured_model(
    respx_mock,
    api_endpoint="http://api-lb:8080",
    status: str = "ready",
):
    respx_mock.post(
        f"{api_endpoint}/v1/api/models/get_version_by_id",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "model_version": {
                    "model_version": {
                        "name": "new-model",
                        "visibility": "private",
                        "workspace_id": 1,
                        "conversion": {
                            "python_version": "3.8",
                            "requirements": [],
                            "framework": "keras",
                        },
                        "id": 1,
                        "image_path": None,
                        "input_schema": None,
                        "output_schema": None,
                        "status": status,
                        "task_id": "7f05c403-dcf4-4ecb-b5ea-28f27aa7eb7b",
                        "file_info": {
                            "version": "ec1ab8e3-923b-40dd-9f77-f20bbe8058b3",
                            "sha": "f7e49538e38bebe066ce8df97bac8be239ae8c7d2733e500c8cd633706ae95a8",
                            "file_name": "simple_model.h5",
                        },
                    },
                    "config": {
                        "id": 1,
                        "model_version_id": 1,
                        "runtime": "keras",
                        "tensor_fields": [],
                        "input_schema": None,
                        "output_schema": None,
                    },
                },
            },
        )
    )


def add_deployment_for_pipeline_responder(
    respx_mock,
    api_endpoint="http://api-lb:8080",
    deployment_id=2,
    deployment_name="pipeline-258146-2",
    deployed=True,
):
    respx_mock.post(
        f"{api_endpoint}/v1/graphql",
        content__contains="query {}".format("GetDeploymentForPipeline"),
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "pipeline_by_pk": {
                        "deployment": {
                            "id": deployment_id,
                            "deploy_id": deployment_name,
                            "deployed": deployed,
                            "engine_config": {
                                "engine": {},
                            },
                        }
                    }
                },
            },
        ),
    )
