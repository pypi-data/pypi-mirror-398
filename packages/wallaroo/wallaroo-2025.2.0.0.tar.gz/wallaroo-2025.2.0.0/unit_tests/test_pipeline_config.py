import base64
import datetime
import hashlib
import json

import httpx
import polars as pl
import pyarrow as pa
import respx

import wallaroo
from wallaroo.model_version import ModelVersion
from wallaroo.pipeline_config import *

from . import testutil
from .reusable_responders import (
    add_default_workspace_responder,
    add_insert_model_config_response_with_config,
)

# TODO: derive this test class from unitttest.TestCase so we can use self.assertXXX etc


class TestPipelineConfig:
    def setup_method(self):
        self.ix = 0
        self.now = datetime.datetime.now()
        self.gql_client = testutil.new_gql_client(
            endpoint="http://api-lb:8080/v1/graphql"
        )
        self.test_client = wallaroo.Client(
            gql_client=self.gql_client,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )

    def test_simple(self):
        pipeline = PipelineConfigBuilder(None, "test")
        assert pipeline.config() == PipelineConfig("test", [])

    def gen_id(self):
        self.ix += 1
        return self.ix

    @respx.mock(assert_all_mocked=False)
    def ccfraud_model(self, variant="baseline", config={}, respx_mock=None):
        model_config = {"runtime": "onnx", **config}

        fake_data = {
            "model_id": f"ccfraud_{variant}",
            "model_version": variant,
            "sha": "ccfraud_sha",
            "file_name": f"ccfraud_{variant}.onnx",
        }

        return self.fake_model(model_config, fake_data, respx_mock=respx_mock)

    @respx.mock(assert_all_mocked=False)
    def fake_model(self, model_config, fake_data, respx_mock):
        add_insert_model_config_response_with_config(
            respx_mock, self.test_client.api_endpoint, self.gen_id(), model_config
        )

        model = ModelVersion(
            self.test_client,
            data={
                "id": self.gen_id(),
                "sha": hashlib.sha256(
                    (json.dumps(model_config) + json.dumps(fake_data)).encode("utf8")
                ).hexdigest(),
                "updated_at": self.now.isoformat(),
                **fake_data,
            },
        )

        model.configure(**model_config)

        # sorry
        model._config._model_version = model

        return model

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def mlflow_model(
        self,
        input_schema,
        output_schema,
        variant="primary",
        runtime="mlflow",
        respx_mock=None,
    ):
        add_default_workspace_responder(respx_mock, self.test_client.api_endpoint)
        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/models/upload").mock(
            return_value=httpx.Response(
                200,
                json={"insert_models": {"returning": [{"models": [{"id": 1}]}]}},
            )
        )

        respx_mock.post(f"{self.test_client.api_endpoint}/v1/graphql").mock(
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
            )
        )

        input_schema_str = base64.b64encode(bytes(input_schema.serialize())).decode(
            "utf8"
        )
        output_schema_str = base64.b64encode(bytes(output_schema.serialize())).decode(
            "utf8"
        )

        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/models/get_version_by_id"
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
                            "status": "ready",
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
                            "runtime": runtime,
                            "input_schema": input_schema_str,
                            "output_schema": output_schema_str,
                            "dynamic_batching_config": None,
                        },
                    }
                },
            )
        )

        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/api/models/insert_model_config"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "model_config": {
                        "id": 1,
                        "model_version_id": 1,
                        "runtime": runtime,
                        "input_schema": input_schema_str,
                        "output_schema": output_schema_str,
                        "dynamic_batching_config": None,
                    },
                },
            )
        )

        respx_mock.post(f"{self.test_client.api_endpoint}/v1/graphql").mock(
            return_value=httpx.Response(
                200,
                json={},
            )
        )

        model = self.test_client.register_model_image(
            "mlflow-primary", "my-image"
        ).configure(
            runtime,
            input_schema=input_schema,
            output_schema=output_schema,
        )

        model._fill(
            {
                "id": 3,
                "model_id": "mlflow-primary",
                "model_version": "n/a",
                "file_name": "none",
                "image_path": "my-image",
                "sha": "sha_sha",
                "updated_at": self.now.isoformat(),
            }
        )
        model._config._fill(
            {
                "id": model._config.id,
                "input_schema": model._config._input_schema,
                "output_schema": model._config._output_schema,
                "runtime": model._config._runtime,
                "model": model._config._model_version,
                "batch_config": None,
                "tensor_fields": None,
                "filter_threshold": None,
                "dynamic_batching_config": None,
            }
        )
        return model

    def assertJsonRoundTrip(self, pipeline: PipelineConfigBuilder):
        config = pipeline.config()
        assert PipelineConfig.from_json(config.to_json()) == config

    def assertModelConfigs(
        self, pipeline: PipelineConfigBuilder, models: Iterable[ModelVersion]
    ):
        active = set(mc.id() for mc in pipeline._model_configs())
        for model in models:
            assert model.config().id() in active

    @respx.mock(assert_all_mocked=False)
    def test_add_models(self, respx_mock):
        pipeline = PipelineConfigBuilder(None, "test")
        one = self.ccfraud_model("one", respx_mock=respx_mock)
        two = self.ccfraud_model("two", respx_mock=respx_mock)

        pipeline.add_multi_model_step([one, two])
        assert pipeline.steps == [
            ModelInference(
                [
                    ModelForStep.from_model(one),
                    ModelForStep.from_model(two),
                ]
            )
        ]
        self.assertModelConfigs(pipeline, [one, two])
        self.assertJsonRoundTrip(pipeline)

    @respx.mock(assert_all_mocked=False)
    def test_remove_step(self, respx_mock):
        pipeline = PipelineConfigBuilder(None, "test")
        one = self.ccfraud_model("one", respx_mock=respx_mock)
        two = self.ccfraud_model("two", respx_mock=respx_mock)

        pipeline.add_model_step(one)
        pipeline.add_multi_model_step([one, two])
        pipeline.remove_step(0)

        assert len(pipeline.model_configs) == 1
        assert pipeline.steps == [
            ModelInference(
                [
                    ModelForStep.from_model(one),
                    ModelForStep.from_model(two),
                ]
            )
        ]

    @respx.mock(assert_all_mocked=False)
    def test_replace_with_model_step(self, respx_mock):
        pipeline = PipelineConfigBuilder(None, "test")
        one = self.ccfraud_model("one", respx_mock=respx_mock)
        two = self.ccfraud_model("two", respx_mock=respx_mock)

        pipeline.add_model_step(one)
        pipeline.add_multi_model_step([one, two])
        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            ModelInference(
                [
                    ModelForStep.from_model(one),
                    ModelForStep.from_model(two),
                ]
            ),
        ]
        assert len(pipeline.model_configs) == 2
        assert len(pipeline._model_configs()) == 3
        pipeline.replace_with_model_step(1, two)

        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            ModelInference([ModelForStep.from_model(two)]),
        ]
        assert len(pipeline.model_configs) == 2
        assert len(pipeline._model_configs()) == 2

    @respx.mock(assert_all_mocked=False)
    def test_replace_with_multi_model_step(self, respx_mock):
        pipeline = PipelineConfigBuilder(None, "test")
        one = self.ccfraud_model("one", respx_mock=respx_mock)
        two = self.ccfraud_model("two", respx_mock=respx_mock)

        pipeline.add_model_step(one)
        pipeline.add_model_step(two)
        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            ModelInference([ModelForStep.from_model(two)]),
        ]
        assert len(pipeline.model_configs) == 2
        assert len(pipeline._model_configs()) == 2
        pipeline.replace_with_multi_model_step(0, [one, two])

        assert pipeline.steps == [
            ModelInference(
                [
                    ModelForStep.from_model(one),
                    ModelForStep.from_model(two),
                ]
            ),
            ModelInference([ModelForStep.from_model(two)]),
        ]
        assert len(pipeline.model_configs) == 2
        assert len(pipeline._model_configs()) == 3

    def test_audit(self):
        pipeline = PipelineConfigBuilder(None, "test")
        one = self.ccfraud_model("one")

        pipeline.add_multi_model_step([one]).add_audit("1")
        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            AuditResults(1, None),
        ]
        self.assertModelConfigs(pipeline, [one])
        self.assertJsonRoundTrip(pipeline)

    def test_replace_with_audit(self):
        pipeline = PipelineConfigBuilder(None, "test")
        one = self.ccfraud_model("one")
        two = self.ccfraud_model("two")
        pipeline.add_model_step(one)
        pipeline.add_model_step(two)
        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            ModelInference([ModelForStep.from_model(two)]),
        ]
        assert len(pipeline.model_configs) == 2
        assert len(pipeline._model_configs()) == 2

        pipeline.replace_with_audit(1, "1")
        assert len(pipeline.model_configs) == 2
        assert len(pipeline._model_configs()) == 1
        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            AuditResults(1, None),
        ]

    def test_key_split(self):
        pipeline = PipelineConfigBuilder(None, "test")
        baseline = self.ccfraud_model("baseline")
        gold_model = self.ccfraud_model("gold")
        pipeline.add_key_split(baseline, "card_type", {"gold": gold_model})
        assert pipeline.steps == [
            MetaValueSplit(
                "card_type",
                ModelForStep.from_model(baseline),
                {"gold": ModelForStep.from_model(gold_model)},
            )
        ]
        self.assertModelConfigs(pipeline, [baseline, gold_model])
        self.assertJsonRoundTrip(pipeline)

    def test_replace_with_key_split(self):
        pipeline = PipelineConfigBuilder(None, "test")
        one = self.ccfraud_model("one")
        two = self.ccfraud_model("two")
        pipeline.add_model_step(one)
        pipeline.add_model_step(two)
        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            ModelInference([ModelForStep.from_model(two)]),
        ]
        assert len(pipeline.model_configs) == 2
        assert len(pipeline._model_configs()) == 2

        baseline = self.ccfraud_model("baseline")
        gold_model = self.ccfraud_model("gold")
        pipeline.replace_with_key_split(1, baseline, "card_type", {"gold": gold_model})
        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            MetaValueSplit(
                "card_type",
                ModelForStep.from_model(baseline),
                {"gold": ModelForStep.from_model(gold_model)},
            ),
        ]
        assert len(pipeline.model_configs) == 2
        assert len(pipeline._model_configs()) == 3

    def test_random_split(self):
        pipeline = PipelineConfigBuilder(None, "test")
        baseline = self.ccfraud_model("a")
        bandit = self.ccfraud_model("b")
        pipeline.add_random_split([(95, baseline), (5, bandit)])
        assert pipeline.steps == [
            RandomSplit(
                [
                    ModelWeight(95, ModelForStep.from_model(baseline)),
                    ModelWeight(5, ModelForStep.from_model(bandit)),
                ]
            )
        ]
        self.assertModelConfigs(pipeline, [baseline, bandit])
        self.assertJsonRoundTrip(pipeline)

    def test_replace_with_random_split(self):
        pipeline = PipelineConfigBuilder(None, "test")
        one = self.ccfraud_model("one")
        two = self.ccfraud_model("two")
        pipeline.add_model_step(one)
        pipeline.add_model_step(two)
        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            ModelInference([ModelForStep.from_model(two)]),
        ]
        assert len(pipeline.model_configs) == 2
        assert len(pipeline._model_configs()) == 2

        baseline = self.ccfraud_model("a")
        bandit = self.ccfraud_model("b")
        pipeline.replace_with_random_split(0, [(95, baseline), (5, bandit)])
        assert pipeline.steps == [
            RandomSplit(
                [
                    ModelWeight(95, ModelForStep.from_model(baseline)),
                    ModelWeight(5, ModelForStep.from_model(bandit)),
                ]
            ),
            ModelInference([ModelForStep.from_model(two)]),
        ]
        assert len(pipeline.model_configs) == 2
        assert len(pipeline._model_configs()) == 3

    def test_shadow_deploy(self):
        pipeline = PipelineConfigBuilder(None, "test")
        baseline = self.ccfraud_model("baseline")
        burn_in = self.ccfraud_model("burn_in")
        pipeline.add_shadow_deploy(baseline, [burn_in])
        assert pipeline.steps == [
            ModelInference(
                [
                    ModelForStep.from_model(baseline),
                    ModelForStep.from_model(burn_in),
                ]
            ),
            AuditResults(1),
            MultiOut(),
        ]
        self.assertModelConfigs(pipeline, [baseline, burn_in])
        self.assertJsonRoundTrip(pipeline)

    def test_replace_with_shadow_deploy(self):
        pipeline = PipelineConfigBuilder(None, "test")
        one = self.ccfraud_model("one")
        two = self.ccfraud_model("two")
        three = self.ccfraud_model("three")
        pipeline.add_model_step(one)
        pipeline.add_model_step(two)
        pipeline.add_model_step(three)
        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            ModelInference([ModelForStep.from_model(two)]),
            ModelInference([ModelForStep.from_model(three)]),
        ]
        assert len(pipeline.model_configs) == 3
        assert len(pipeline._model_configs()) == 3

        baseline = self.ccfraud_model("baseline")
        burn_in = self.ccfraud_model("burn_in")
        pipeline.replace_with_shadow_deploy(1, baseline, [burn_in])
        assert pipeline.steps == [
            ModelInference([ModelForStep.from_model(one)]),
            ModelInference(
                [
                    ModelForStep.from_model(baseline),
                    ModelForStep.from_model(burn_in),
                ]
            ),
            AuditResults(1),
            MultiOut(),
            ModelInference([ModelForStep.from_model(three)]),
        ]
        assert len(pipeline.model_configs) == 5
        assert len(pipeline._model_configs()) == 4

    def test_simple_pipeline(self, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")
        ccfraud = self.ccfraud_model("keras")

        pipeline.add_model_step(ccfraud)

        self.assertModelConfigs(pipeline, [ccfraud])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(ccfraud._config.to_k8s_yaml(), "model_config.yaml")

    def test_batch_config_pipeline(self, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")
        ccfraud = self.ccfraud_model("keras", config={"batch_config": "single"})

        pipeline.add_model_step(ccfraud)

        self.assertModelConfigs(pipeline, [ccfraud])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(ccfraud._config.to_k8s_yaml(), "model_config.yaml")

    def test_py_pipeline(self, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")

        wl_model = self.fake_model(
            {"runtime": "onnx", "tensor_fields": ["tensor"]},
            {
                "model_id": "demandcurve",
                "model_version": "0",
                "file_name": "demand_curve_made_here.onnx",
            },
        )

        model_config = {
            "runtime": "python",
        }
        model_pre = self.fake_model(
            model_config,
            {
                "model_id": "preprocess",
                "model_version": "0",
                "file_name": "day5_preprocess.py",
            },
        )
        model_post = self.fake_model(
            model_config,
            {
                "model_id": "postprocess",
                "model_version": "0",
                "file_name": "day5_postprocess.py",
            },
        )

        pipeline = (
            pipeline.add_model_step(model_pre)
            .add_model_step(wl_model)
            .add_model_step(model_post)
        )

        self.assertModelConfigs(pipeline, [model_pre, wl_model, model_post])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(model_pre._config.to_k8s_yaml(), "pre_model_config.yaml")
        snapshot.assert_match(wl_model._config.to_k8s_yaml(), "wl_model_config.yaml")
        snapshot.assert_match(
            model_post._config.to_k8s_yaml(), "post_model_config.yaml"
        )

    def test_ab_pipeline(self, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")

        keras_file = "keras_ccfraud.onnx"
        default_model = self.fake_model(
            {"runtime": "onnx"},
            {
                "model_id": "keras_ccfraud",
                "model_version": "0",
                "file_name": keras_file,
            },
        )

        experiment_file = "modelA.onnx"
        experiment_model = self.fake_model(
            {"runtime": "onnx", "tensor_fields": ["dense_input"]},
            {
                "model_id": "experiment",
                "model_version": "0",
                "file_name": experiment_file,
            },
        )

        meta_key_name = "card_type"
        pipeline = pipeline.add_key_split(
            default_model, meta_key_name, {"gold": experiment_model}
        )

        self.assertModelConfigs(pipeline, [default_model, experiment_model])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(
            default_model._config.to_k8s_yaml(), "default_model_config.yaml"
        )
        snapshot.assert_match(
            experiment_model._config.to_k8s_yaml(), "experiment_model_config.yaml"
        )

    def test_random_split_pipeline(self, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")

        # due to how the engine handles tensorflow and local files, the model
        # name must include .zip and be identical to the file name :sadlol:
        control = self.fake_model(
            {"runtime": "tensorflow"},
            {
                "model_id": "aloha-cnn-lstm.zip",
                "model_version": "0",
                "file_name": "aloha-cnn-lstm.zip",
            },
        )
        challenger = self.fake_model(
            {"runtime": "tensorflow"},
            {
                "model_id": "aloha-cnn-lstm-new.zip",
                "model_version": "0",
                "file_name": "aloha-cnn-lstm-new.zip",
            },
        )
        pipeline = pipeline.add_random_split(
            [(2, control), (1, challenger)], "session_id"
        )

        self.assertModelConfigs(pipeline, [control, challenger])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(control._config.to_k8s_yaml(), "control.yaml")
        snapshot.assert_match(challenger._config.to_k8s_yaml(), "challenger.yaml")

    def test_shadow_deploy_pipeline(self, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")

        keras_file = "keras_ccfraud.onnx"
        champion = self.fake_model(
            {"runtime": "onnx"},
            {
                "model_id": "keras_ccfraud",
                "model_version": "0",
                "file_name": keras_file,
            },
        )

        keras_file = "keras_xgboost.onnx"
        model2 = self.fake_model(
            {"runtime": "onnx", "tensor_fields": ["dense_input"]},
            {
                "model_id": "ccfraudxgb",
                "model_version": "0",
                "file_name": keras_file,
            },
        )

        experiment_file = "modelA.onnx"
        model3 = self.fake_model(
            {"runtime": "onnx", "tensor_fields": ["dense_input"]},
            {
                "model_id": "ccfraudrf",
                "model_version": "0",
                "file_name": experiment_file,
            },
        )

        pipeline.add_shadow_deploy(champion, [model2, model3])

        self.assertModelConfigs(pipeline, [champion, model2, model3])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(champion._config.to_k8s_yaml(), "control.yaml")
        snapshot.assert_match(model2._config.to_k8s_yaml(), "model2.yaml")
        snapshot.assert_match(model3._config.to_k8s_yaml(), "model3.yaml")

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_mlflow_pipeline(self, respx_mock, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")
        input_schema = pa.schema(
            [
                pa.field("temp", pa.float32()),
                pa.field("holiday", pa.uint8()),
                pa.field("workingday", pa.uint8()),
                pa.field("windspeed", pa.float32()),
            ]
        )

        output_schema = pa.schema([pa.field("sum", pa.float32())])
        mlflow = self.mlflow_model(input_schema, output_schema, respx_mock=respx_mock)

        pipeline.add_model_step(mlflow)

        self.assertModelConfigs(pipeline, [mlflow])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(mlflow.config().to_k8s_yaml(), "model_config.yaml")

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_mlflow_struct_pipeline(self, respx_mock, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")
        input_schema = pa.schema(
            [
                pa.field(
                    "inputs", pa.list_(pa.float32())
                ),  # required: the audio stored in numpy arrays of shape (num_samples,) and data type `float32`
                pa.field(
                    "return_timestamps", pa.string()
                ),  # optional: return start & end times for each predicted chunk
            ]
        )

        output_schema = pa.schema(
            [
                pa.field(
                    "text", pa.string()
                ),  # required: the output text corresponding to the audio input
                pa.field(
                    "chunks",
                    pa.list_(
                        pa.struct(
                            [
                                ("text", pa.string()),
                                ("timestamp", pa.list_(pa.float32())),
                            ]
                        )
                    ),
                ),  # required (if `return_timestamps` is set), start & end times for each predicted chunk
            ]
        )

        mlflow = self.mlflow_model(
            input_schema, output_schema, runtime="flight", respx_mock=respx_mock
        )

        pipeline.add_model_step(mlflow)

        self.assertModelConfigs(pipeline, [mlflow])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(mlflow.config().to_k8s_yaml(), "model_config.yaml")

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_flight_nullable_pipeline(self, respx_mock, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")

        input_schema = pa.schema(
            [
                pa.field("input_1", pa.list_(pa.float32()), nullable=False),
                pa.field("input_2", pa.list_(pa.float32()), nullable=True),
                pa.field("multiply_factor", pa.int32()),
            ]
        )

        output_schema = pa.schema(
            [
                pa.field("output", pa.list_(pa.float32())),
            ]
        )

        mlflow = self.mlflow_model(
            input_schema, output_schema, runtime="flight", respx_mock=respx_mock
        )

        pipeline.add_model_step(mlflow)

        self.assertModelConfigs(pipeline, [mlflow])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(mlflow.config().to_k8s_yaml(), "model_config.yaml")

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_flight_cv_pipeline(self, respx_mock, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")

        input_schema = pa.schema(
            [
                pa.field(
                    "tensor",
                    pa.list_(
                        pa.list_(
                            pa.list_(
                                pa.list_(
                                    pa.float32(),  # images are normalized
                                    list_size=640,
                                ),
                                list_size=480,
                            ),
                            list_size=3,
                        ),
                        list_size=1,
                    ),
                ),
            ]
        )

        output_schema = pa.schema(
            [
                pa.field("boxes", pa.list_(pa.list_(pa.float32(), list_size=4))),
                pa.field("classes", pa.list_(pa.int64())),
                pa.field("confidences", pa.list_(pa.float32())),
                pa.field("avg_px_intensity", pa.list_(pa.float32())),
                pa.field("avg_confidence", pa.list_(pa.float32())),
            ]
        )

        mlflow = self.mlflow_model(
            input_schema, output_schema, runtime="flight", respx_mock=respx_mock
        )

        pipeline.add_model_step(mlflow)

        self.assertModelConfigs(pipeline, [mlflow])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(mlflow.config().to_k8s_yaml(), "model_config.yaml")

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_large_arrays(self, respx_mock, snapshot):
        input_schema = pa.schema(
            [
                pa.field("array1", pa.list_(pa.float32())),
                pa.field("array2", pa.list_(pa.float32())),
                pa.field("array3", pa.list_(pa.float32())),
                pa.field("dim0", pa.int64()),
                pa.field("dim1", pa.int64()),
            ]
        )

        output_schema = pa.schema([pa.field("result", pa.float32())])

        sidekick = self.mlflow_model(
            input_schema, output_schema, runtime="flight", respx_mock=respx_mock
        )

        pipeline = PipelineConfigBuilder(None, "test")

        pipeline.add_model_step(sidekick)

        self.assertModelConfigs(pipeline, [sidekick])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(sidekick.config().to_k8s_yaml(), "model_config.yaml")

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_fixed_tensor(self, respx_mock, snapshot):
        input_schema = pa.schema(
            [
                pa.field("tensor_i", pa.fixed_shape_tensor(pa.float32(), [4, 4])),
            ]
        )

        output_schema = pa.schema(
            [pa.field("tensor_o", pa.fixed_shape_tensor(pa.float32(), [4, 4]))]
        )

        sidekick = self.mlflow_model(
            input_schema, output_schema, runtime="flight", respx_mock=respx_mock
        )

        pipeline = PipelineConfigBuilder(None, "test")

        pipeline.add_model_step(sidekick)

        self.assertModelConfigs(pipeline, [sidekick])
        self.assertJsonRoundTrip(pipeline)

        # XXX - these schema snapshots are not deterministic for some annoying reason.
        # Uncomment to regenerate.
        # snapshot.assert_match(sidekick.config().to_k8s_yaml(), "model_config.yaml")

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_mlflow_variable_pipeline(self, snapshot, respx_mock):
        pipeline = PipelineConfigBuilder(None, "test")
        input_schema = pa.schema(
            [
                pa.field("vec0", pa.list_(pa.float32())),
                pa.field("vec1", pa.list_(pa.float32())),
            ]
        )

        output_schema = pa.schema([pa.field("matrix", pa.list_(pa.float32()))])
        mlflow = self.mlflow_model(input_schema, output_schema, respx_mock=respx_mock)

        pipeline.add_model_step(mlflow)

        self.assertModelConfigs(pipeline, [mlflow])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(mlflow._config.to_k8s_yaml(), "model_config.yaml")

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_mlflow_multidim_pipeline(self, respx_mock, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")
        input_schema = pa.schema(
            [
                pa.field("img", pa.list_(pa.list_(pa.list_(pa.float32())))),
            ]
        )

        output_schema = pa.schema(
            [pa.field("bounds", pa.list_(pa.list_(pa.uint32(), 4)))]
        )
        mlflow = self.mlflow_model(input_schema, output_schema, respx_mock=respx_mock)

        pipeline.add_model_step(mlflow)

        self.assertModelConfigs(pipeline, [mlflow])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(mlflow._config.to_k8s_yaml(), "model_config.yaml")

    @respx.mock(assert_all_mocked=False, assert_all_called=False)
    def test_demandgen_mlflow_pipeline(self, respx_mock, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")
        input_schema = pa.schema(
            [
                pa.field("site_id", pa.string()),
                pa.field("channel_id", pa.string()),
                pa.field("product_id", pa.string()),
                pa.field("v0", pa.float64()),
                pa.field("v1", pa.float64()),
                pa.field("v2", pa.float64()),
                pa.field("v3", pa.float64()),
                pa.field("v4", pa.float64()),
                pa.field("v5", pa.float64()),
                pa.field("v6", pa.float64()),
                pa.field("v7", pa.float64()),
                pa.field("v8", pa.float64()),
                pa.field("v9", pa.float64()),
                pa.field("v10", pa.float64()),
                pa.field("v11", pa.float64()),
                pa.field("v12", pa.float64()),
                pa.field("v13", pa.float64()),
                pa.field("v14", pa.float64()),
                pa.field("v15", pa.float64()),
                pa.field("v16", pa.float64()),
                pa.field("v17", pa.float64()),
                pa.field("v18", pa.float64()),
                pa.field("v19", pa.float64()),
            ]
        )

        output_schema = pa.schema(
            [
                pa.field("site_id", pa.string()),
                pa.field("channel_id", pa.string()),
                pa.field("product_id", pa.string()),
                pa.field("v0", pa.list_(pa.float64(), 6)),
                pa.field("outcome", pa.list_(pa.float64(), 6)),
            ]
        )
        mlflow = self.mlflow_model(input_schema, output_schema, respx_mock=respx_mock)

        pipeline.add_model_step(mlflow)

        self.assertModelConfigs(pipeline, [mlflow])
        self.assertJsonRoundTrip(pipeline)

        snapshot.assert_match(mlflow._config.to_k8s_yaml(), "model_config.yaml")

    @respx.mock(assert_all_mocked=False)
    def test_validate(self, respx_mock, snapshot):
        pipeline = PipelineConfigBuilder(None, "test")
        baseline = self.ccfraud_model("a", respx_mock=respx_mock)
        bandit = self.ccfraud_model("b", respx_mock=respx_mock)
        baseline_ok = pl.col("tensor") > 0.95
        bandit_ok = pl.col("tensor") > 0.95
        (
            pipeline.add_random_split([(95, baseline), (5, bandit)]).add_validations(
                bandit_ok=bandit_ok, baseline_ok=baseline_ok
            )
        )

        self.assertModelConfigs(pipeline, [baseline, bandit])
        self.assertJsonRoundTrip(pipeline)
        snapshot.assert_match(
            json.dumps(pipeline.config().to_json(), indent=4), "single_validation.json"
        )

    @respx.mock(assert_all_mocked=False)
    def test_single_validation(self, respx_mock, snapshot):
        p = PipelineConfigBuilder(None, "test")
        baseline = self.ccfraud_model("base", respx_mock=respx_mock)
        p = p.add_model_step(baseline)
        p = p.add_validations(positive=pl.col("out.dense_1").list.get(0) > 0)

        self.assertModelConfigs(p, [baseline])
        self.assertJsonRoundTrip(p)

        snapshot.assert_match(baseline._config.to_k8s_yaml(), "model_config.yaml")

    @respx.mock(assert_all_mocked=False)
    def test_clear(self, respx_mock):
        pipeline = PipelineConfigBuilder(None, "test")
        one = self.ccfraud_model("one", respx_mock=respx_mock)
        two = self.ccfraud_model("two", respx_mock=respx_mock)
        pipeline.add_multi_model_step([one, two])

        result = pipeline.clear()
        self.assertJsonRoundTrip(pipeline)
        assert isinstance(result, PipelineConfigBuilder)
        assert pipeline.steps == []
        self.assertModelConfigs(pipeline, [])

    def test_name_check(self):
        try:
            pipeline = PipelineConfigBuilder(None, "bad_dns")
            assert False
        except RuntimeError:
            pass
        except Exception:
            assert False

        pipeline2 = PipelineConfigBuilder(None, "good-dns")
        assert True
