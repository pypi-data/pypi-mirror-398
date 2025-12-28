import json
import os
import sys
from datetime import datetime, timezone
from io import StringIO
from unittest import mock

import httpx
import numpy
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest
import respx

import wallaroo
from wallaroo.deployment_config import DeploymentConfigBuilder
from wallaroo.model_config import ModelConfig
from wallaroo.model_version import ModelVersion
from wallaroo.pipeline import Pipeline
from wallaroo.pipeline_version import PipelineVersion
from wallaroo.tag import Tag

from . import status_samples, testutil
from .reusable_responders import (
    add_create_pipeline_responder,
    add_deploy_test_responders,
    add_deployment_by_id_responder,
    add_deployment_for_pipeline_responder,
    add_deployment_status_responder,
    add_get_pipeline_by_id_responder,
    add_pipeline_by_id_responder,
    add_pipeline_variant_by_id_responder,
)

sink = pa.BufferOutputStream()
with pa.ipc.open_file("unit_tests/outputs/sample_logs.arrow") as reader:
    arrow_logs = reader.read_all()
    with pa.ipc.new_file(sink, arrow_logs.schema) as arrow_ipc:
        arrow_ipc.write(arrow_logs)
        arrow_ipc.close()

sample_sink = pa.BufferOutputStream()
with pa.ipc.open_file(
    "unit_tests/outputs/sample_record_limited_infer_log.arrow"
) as reader:
    sample_logs = reader.read_all()
    with pa.ipc.new_file(sample_sink, sample_logs.schema) as a_ipc:
        a_ipc.write(sample_logs)
        a_ipc.close()

schema_changed_sink = pa.BufferOutputStream()
with pa.ipc.open_file(
    "unit_tests/outputs/sample_schema_change_infer_log.arrow"
) as reader:
    arrow_logs = reader.read_all()
    with pa.ipc.new_file(schema_changed_sink, arrow_logs.schema) as arrow_ipc:
        arrow_ipc.write(arrow_logs)
        arrow_ipc.close()

dropped_log_sink = pa.BufferOutputStream()
with pa.ipc.open_file("unit_tests/outputs/tensor_dropped_log_file.arrow") as tdl_reader:
    tensor_dropped_logs = tdl_reader.read_all()
    with pa.ipc.new_file(dropped_log_sink, tensor_dropped_logs.schema) as tdl_ipc:
        tdl_ipc.write(tensor_dropped_logs)
        tdl_ipc.close()

SAMPLE_ARROW_LOGS_RESPONSE = sink.getvalue()
SAMPLE_PANDAS_RECORDS_INFERENCE_RESPONSE = json.load(
    open("unit_tests/outputs/sample_inference_result.pandas.json", "rb")
)
with open("unit_tests/outputs/parallel_infer_data.pandas.json", "r") as fp:
    SAMPLE_PANDAS_RECORDS_JSON = pd.read_json(fp)
with open("unit_tests/outputs/batch_parallel_infer_data.pandas.json", "r") as fp:
    SAMPLE_PANDAS_RECORDS_JSON_PARALLEL_BATCH = pd.read_json(fp)


class TestPipeline:
    def setup_method(self):
        self.ix = 0
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
        self.pipeline = Pipeline(
            client=self.test_client,
            data={
                "id": 1,
                "pipeline_id": "x",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat(),
                "pipeline_versions": [{"id": 1}],
                "visibility": "pUbLIC",
            },
        )

    def gen_id(self):
        self.ix += 1
        return self.ix

    def ccfraud_model(self, variant="some_model_variant_name"):
        data = {
            "id": self.gen_id(),
            "model_id": "some_model_name",
            "model_version": variant,
            "sha": "ccfraud_sha",
            "file_name": "some_model_file.onnx",
            "updated_at": self.now.isoformat(),
            "visibility": "private",
        }

        model = ModelVersion(
            client=self.test_client,
            data=data,
        )
        model._config = ModelConfig(
            client=self.test_client,
            data={
                "id": self.gen_id(),
                "model": {
                    "id": model.id(),
                },
                "runtime": "onnx",
                "tensor_fields": "foo bar baz",
            },
        )
        model._config._model_version = model
        return model

    def add_pipeline_variant_by_id_responder(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("PipelineVariantById"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "pipeline_version_by_pk": {
                            "id": 2,
                            "created_at": self.now.isoformat(),
                            "updated_at": self.now.isoformat(),
                            "version": "v1",
                            "definition": {
                                "id": "test-pipeline",
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
            )
        )

    def add_pipeline_models_responder(self, respx_mock):
        respx_mock.post(
            "http://api-lb:8080/v1/graphql",
            content__contains="query {}".format("PipelineModels"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "pipeline_by_pk": {
                            "id": 3,
                            "deployment": {
                                "deployment_model_configs_aggregate": {
                                    "nodes": [
                                        {
                                            "model_config": {
                                                "model": {
                                                    "model": {"name": "ccfraud1-258146"}
                                                }
                                            }
                                        },
                                        {
                                            "model_config": {
                                                "model": {
                                                    "model": {"name": "ccfraud2-258146"}
                                                }
                                            }
                                        },
                                    ]
                                },
                            },
                        },
                    }
                },
            )
        )

    @staticmethod
    def add_get_topic_name_responder(respx_mock):
        respx_mock.post("http://api-lb:8080/v1/api/plateau/get_topic_name").mock(
            return_value=httpx.Response(
                200, json={"topic_name": "workspace-1-pipeline-x-inference"}
            )
        )

    @staticmethod
    def add_get_records_responder(params, respx_mock):
        respx_mock.post(
            "http://api-lb:8080/v1/logs/topic/workspace-1-pipeline-x-inference/records",
        ).mock(
            return_value=httpx.Response(
                200,
                content=bytes(sink.getvalue()),
            )
        )

    @staticmethod
    def add_get_record_limited_records_responder(params, respx_mock):
        respx_mock.post(
            "http://api-lb:8080/v1/logs/topic/workspace-1-pipeline-x-inference/records",
        ).mock(
            return_value=httpx.Response(
                200,
                content=bytes(sample_sink.getvalue()),
            )
        )

    @staticmethod
    def add_get_records_with_schema_change_responder(params, respx_mock):
        respx_mock.post(
            "http://api-lb:8080/v1/logs/topic/workspace-1-pipeline-x-inference/records",
            params=params,
        ).mock(
            side_effect=[
                httpx.Response(
                    200,
                    content=bytes(schema_changed_sink.getvalue()),
                ),
                httpx.Response(
                    200,
                    content=bytes(sample_sink.getvalue()),
                ),
            ]
        )

    @staticmethod
    def add_get_tensor_dropped_records_responder(params, respx_mock):
        respx_mock.post(
            "http://api-lb:8080/v1/logs/topic/workspace-1-pipeline-x-inference/records",
        ).mock(
            return_value=httpx.Response(
                200,
                content=bytes(dropped_log_sink.getvalue()),
            )
        )

    def test_init_full_dict(self):
        pipeline = Pipeline(
            client=self.test_client,
            data={
                "id": 1,
                "pipeline_id": "test-pipeline",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat(),
                "pipeline_versions": [{"id": 1}],
                "visibility": "pUbLIC",
            },
        )

        assert 1 == pipeline.id()
        assert "test-pipeline" == pipeline.name()
        assert self.now == pipeline.create_time()
        assert self.now == pipeline.last_update_time()
        assert isinstance(pipeline.versions()[0], PipelineVersion)

    @respx.mock(assert_all_mocked=True)
    def test_html_repr(self, respx_mock):
        add_pipeline_by_id_responder(respx_mock)
        add_deployment_for_pipeline_responder(respx_mock)
        self.add_pipeline_models_responder(respx_mock)
        self.add_pipeline_variant_by_id_responder(respx_mock)
        # add_get_workspace_by_id_responder(respx_mock, self.test_client.api_endpoint)

        model1 = self.ccfraud_model("one")
        model2 = self.ccfraud_model("two")
        p = self.pipeline.add_model_step(model1)
        p = p.add_model_step(model2)

        hstr = p._repr_html_()
        assert "<table>" in hstr

    @pytest.mark.parametrize(
        "method_name, want_value",
        [
            ("name", "test-pipeline"),
            ("create_time", datetime(2024, 1, 1, 0, 0, 0)),
            ("last_update_time", datetime(2024, 2, 1, 0, 0, 0)),
            ("versions", None),
        ],
    )
    @respx.mock
    def test_rehydrate(self, method_name, want_value, respx_mock):
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
                            "pipeline_id": "test-pipeline",
                            "created_at": datetime(2024, 1, 1, 0, 0, 0).isoformat(),
                            "updated_at": datetime(2024, 2, 1, 0, 0, 0).isoformat(),
                            "pipeline_versions": [{"id": 1}],
                            "visibility": "pUbLIC",
                        }
                    },
                },
            )
        )

        pipeline = Pipeline(client=self.test_client, data={"id": 1})
        got_value = getattr(pipeline, method_name)()

        if want_value is not None:
            assert want_value == got_value
        assert 1 == respx_mock.calls.call_count
        # Another call to the same accessor shouldn't trigger any
        # additional GraphQL queries.
        got_value = getattr(pipeline, method_name)()
        if want_value is not None:
            assert want_value == got_value
        assert 1 == respx_mock.calls.call_count
        respx_mock.reset()

    @respx.mock(assert_all_mocked=True)
    def test_logs_with_arrow(self, respx_mock):
        params = {
            "page_size": 100,
            "order": "desc",
            "dataset[]": "*",
            "dataset.separator": ".",
        }
        self.add_get_topic_name_responder(respx_mock)
        self.add_get_records_responder(params, respx_mock)
        log_table = self.pipeline.logs(limit=100, arrow=True)

        assert isinstance(log_table, pa.Table)
        log_table.equals(arrow_logs)

    @respx.mock(assert_all_mocked=True)
    def test_tensor_dropped_logs_with_arrow(self, respx_mock):
        params = {
            "page_size": 100,
            "order": "desc",
            "dataset[]": "*",
            "dataset.separator": ".",
        }
        self.add_get_topic_name_responder(respx_mock)
        self.add_get_tensor_dropped_records_responder(params, respx_mock)
        log_table_df = self.pipeline.logs(limit=100)
        assert isinstance(log_table_df, pd.DataFrame)
        assert log_table_df["in.tensor"][0] is None  # tensor dropped

    @respx.mock(assert_all_mocked=True)
    def test_export_logs_to_arrow_file(self, respx_mock):
        start_datetime = datetime.now(timezone.utc).replace(tzinfo=None)
        end_datetime = datetime.now(timezone.utc).replace(tzinfo=None)
        params = {
            "time.start": start_datetime.astimezone(tz=timezone.utc).isoformat(),
            "time.end": end_datetime.astimezone(tz=timezone.utc).isoformat(),
            "dataset[]": "*",
            "dataset[]": "*",
            "dataset.separator": ".",
        }
        self.add_get_topic_name_responder(respx_mock)
        self.add_get_records_responder(params, respx_mock)

        self.pipeline.export_logs(
            directory="unit_tests/outputs",
            file_prefix="test_logs",
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            arrow=True,
        )
        with pa.ipc.open_file("unit_tests/outputs/test_logs-1.arrow") as file_reader:
            entries = file_reader.read_all()
        arrow_logs.equals(entries, check_metadata=True)

    @respx.mock(assert_all_mocked=True)
    def test_export_logs_without_user_provided_filepath(self, respx_mock):
        start_datetime = datetime.now(timezone.utc).replace(tzinfo=None)
        end_datetime = datetime.now(timezone.utc).replace(tzinfo=None)
        params = {
            "time.start": start_datetime.astimezone(tz=timezone.utc).isoformat(),
            "time.end": end_datetime.astimezone(tz=timezone.utc).isoformat(),
            "dataset[]": "*",
            "dataset.separator": ".",
        }
        self.add_get_topic_name_responder(respx_mock)
        self.add_get_records_responder(params, respx_mock)
        cwd = os.getcwd()
        # we don't want to be writing test related files outside this directory
        os.chdir("unit_tests/outputs")
        self.pipeline.export_logs(
            start_datetime=start_datetime, end_datetime=end_datetime, arrow=True
        )
        with pa.ipc.open_file(f"logs/{self.pipeline.name()}-1.arrow") as file_reader:
            entries = file_reader.read_all()
        arrow_logs.equals(entries, check_metadata=True)
        os.chdir(cwd)

    @respx.mock(assert_all_mocked=True)
    def test_get_pipeline_logs_by_time(self, respx_mock):
        start_datetime = datetime.now(timezone.utc).replace(tzinfo=None)
        end_datetime = datetime.now(timezone.utc).replace(tzinfo=None)
        params = {
            "time.start": start_datetime.astimezone(tz=timezone.utc).isoformat(),
            "time.end": end_datetime.astimezone(tz=timezone.utc).isoformat(),
            "dataset[]": "*",
            "dataset.separator": ".",
        }
        self.add_get_topic_name_responder(respx_mock)
        self.add_get_records_responder(params, respx_mock)

        log_table = self.pipeline.logs(
            start_datetime=start_datetime, end_datetime=end_datetime, arrow=True
        )
        assert isinstance(log_table, pa.Table)
        log_table.equals(arrow_logs)

    @mock.patch("sys.stderr", new_callable=StringIO)
    @respx.mock(assert_all_mocked=True)
    def test_pipeline_export_logs_with_schema_change(self, stdout, respx_mock):
        log_directory = "unit_tests/outputs/logs/"
        log_file_prefix = "unittest"
        start_datetime = datetime.now(timezone.utc).replace(tzinfo=None)
        end_datetime = datetime.now(timezone.utc).replace(tzinfo=None)
        params = {
            "time.start": start_datetime.astimezone(tz=timezone.utc).isoformat(),
            "time.end": end_datetime.astimezone(tz=timezone.utc).isoformat(),
            "dataset[]": "*",
            "dataset.separator": ".",
        }
        self.add_get_topic_name_responder(respx_mock)
        self.add_get_records_with_schema_change_responder(params, respx_mock)

        self.pipeline.export_logs(
            directory=log_directory,
            file_prefix=log_file_prefix,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            arrow=True,
        )
        expected_string = (
            "Warning: There are more logs available. Please set a larger limit to export "
            "more data.\n"
            "\n"
            "Note: The logs with different schemas are written to separate files in the "
            "provided directory."
        )
        assert expected_string == sys.stderr.getvalue()
        assert 3 == respx_mock.calls.call_count
        files_in_directory = os.listdir(log_directory)

        # Check if two files with the specified prefix were written
        matching_files = [
            file for file in files_in_directory if file.startswith(log_file_prefix)
        ]
        assert len(matching_files) == 2

    def test_pipeline_building(self):
        model = self.ccfraud_model()
        p = self.pipeline.add_model_step(model)
        p = p.add_validations(
            no_high_fraud=pl.col("tensor") < 0.9,
            really_no_high_fraud=pl.col("tensor") < 0.95,
        )

        assert len(p.steps()) == 2

    # This can't work yet
    # def test_pipeline_clear(self):
    #     pipeline = Pipeline(
    #         client=self.test_client,
    #         data={
    #             "id": 1,
    #             "pipeline_id": "x",
    #             "created_at": self.now.isoformat(),
    #             "updated_at": self.now.isoformat(),
    #             "pipeline_versions": [{"id": 1}],
    #             "visibility": "PUBLIC",
    #         },
    #     )
    #     one = self.ccfraud_model("one")
    #     two = self.ccfraud_model("two")
    #     pipeline.add_model_step(one)
    #     pipeline.add_model_step(two)
    #     self.assertEqual(len(pipeline.steps()), 2)
    #     self.assertEqual(len(pipeline.model_configs()), 2)

    #     result = pipeline.clear()
    #     assert isinstance(result, Pipeline)
    #     self.assertEqual(pipeline.steps(), [])
    #     self.assertEqual(pipeline.model_configs(), [])

    @respx.mock(assert_all_mocked=True)
    def test_pipeline_tags(self, respx_mock):
        tag_1 = Tag(client=self.test_client, data={"id": 1, "tag": "bartag314"})
        tag_2 = Tag(client=self.test_client, data={"id": 2, "tag": "footag123"})

        respx_mock.post(
            "http://api-lb:8080/v1/graphql",
            content__contains="query {}".format("PipelineById"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "pipeline_by_pk": {
                            "id": 1,
                            "pipeline_id": "test-pipeline",
                            "created_at": self.now.isoformat(),
                            "updated_at": self.now.isoformat(),
                            "pipeline_versions": [{"id": 1}],
                            "visibility": "pUbLIC",
                            "pipeline_tags": [
                                {"tag": {"id": 1, "tag": "bartag314"}},
                                {"tag": {"id": 2, "tag": "footag123"}},
                            ],
                        }
                    },
                },
            )
        )

        pipeline = Pipeline(client=self.test_client, data={"id": 1})
        assert list(map(vars, [tag_1, tag_2])) == list(map(vars, pipeline.tags()))

    @respx.mock(assert_all_called=False)
    def test_deploy_success_returns_running_pipeline_object(self, respx_mock):
        add_deploy_test_responders(
            respsx_mock=respx_mock,
            workspace_name="foo-workspace",
            pipeline_name="foo-deployment",
        )
        add_get_pipeline_by_id_responder(
            respx_mock, self.test_client.api_endpoint, "foo-deployment"
        )
        add_create_pipeline_responder(
            respx_mock, api_endpoint=self.test_client.api_endpoint
        )
        add_pipeline_variant_by_id_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            pipeline_id="foo-deployment",
        )
        dc = DeploymentConfigBuilder().build()
        add_deployment_status_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            deployment_name="foo-deployment-10",
            status=status_samples.RUNNING,
        )
        # default workflow
        pipeline = self.pipeline.deploy("foo-deployment", deployment_config=dc)

        assert 1 == pipeline.id()
        assert "foo-deployment" == pipeline.name()
        assert "Running" == pipeline.status()["status"]

    @respx.mock(assert_all_called=False)
    def test_deploy_do_not_wait_for_status_returns_starting_pipeline_object(
        self, respx_mock
    ):
        add_deploy_test_responders(
            respsx_mock=respx_mock,
            workspace_name="foo-workspace",
            pipeline_name="foo-deployment",
        )
        add_get_pipeline_by_id_responder(
            respx_mock, self.test_client.api_endpoint, "foo-deployment"
        )
        add_create_pipeline_responder(
            respx_mock, api_endpoint=self.test_client.api_endpoint
        )
        dc = DeploymentConfigBuilder().build()
        add_deployment_status_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            deployment_name="foo-deployment-10",
            status=status_samples.STARTING,
        )
        add_pipeline_variant_by_id_responder(
            respx_mock,
            api_endpoint=self.test_client.api_endpoint,
            pipeline_id="foo-deployment",
        )
        pipeline = self.pipeline.deploy(
            "foo-deployment", deployment_config=dc, wait_for_status=False
        )

        assert pipeline.id() == 1
        assert pipeline.name() == "foo-deployment"
        assert pipeline.status()["status"] == "Starting"


class TestPipelineAsync:
    def setup_method(self) -> None:
        self.id = 0
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
        self.pipeline = Pipeline(
            client=self.test_client,
            data={
                "id": 1,
                "pipeline_id": "some-pipeline",
                "created_at": self.now.isoformat(),
                "updated_at": self.now.isoformat(),
                "pipeline_versions": [{"id": 1}],
                "visibility": "pUbLIC",
            },
        )

    @respx.mock
    @pytest.mark.asyncio()
    async def test_async_infer(self, respx_mock):
        async with httpx.AsyncClient() as client:
            async_infer_route = respx.post(
                "http://engine-lb.pipeline-258146-2-2:29502/pipelines/some-pipeline",
            ).mock(
                return_value=httpx.Response(
                    200, json=SAMPLE_PANDAS_RECORDS_INFERENCE_RESPONSE
                )
            )
            add_deployment_for_pipeline_responder(
                respx_mock, self.test_client.api_endpoint
            )
            add_deployment_by_id_responder(respx_mock, self.test_client.api_endpoint)
            output_df = await self.pipeline.async_infer(
                tensor=SAMPLE_PANDAS_RECORDS_JSON, async_client=client
            )
            assert isinstance(output_df, pd.DataFrame)
            assert type(output_df["time"][0]) == pd.Timestamp
            assert type(output_df["check_failures"][0]) == numpy.int64
            assert async_infer_route.called
            assert async_infer_route.call_count == 1

    @respx.mock
    @pytest.mark.asyncio()
    async def test_batch_parallel_infer_with_none(self, respx_mock):
        add_deployment_for_pipeline_responder(respx_mock, self.test_client.api_endpoint)
        add_deployment_by_id_responder(respx_mock, self.test_client.api_endpoint)
        with pytest.raises(ValueError):
            await self.pipeline.parallel_infer(
                tensor=None, batch_size=2, num_parallel=3
            )

    @respx.mock
    @pytest.mark.asyncio()
    async def test_batch_parallel_infer_with_json(self, respx_mock):
        add_deployment_for_pipeline_responder(respx_mock, self.test_client.api_endpoint)
        add_deployment_by_id_responder(respx_mock, self.test_client.api_endpoint)
        with pytest.raises(ValueError):
            await self.pipeline.parallel_infer(
                tensor=SAMPLE_PANDAS_RECORDS_JSON.to_json(),
                batch_size=2,
                num_parallel=3,
            )

    @respx.mock
    @pytest.mark.asyncio()
    async def test_batch_parallel_infer_with_pandas_df(self, respx_mock):
        respx.post(
            "http://engine-lb.some-pipeline-1:29502/pipelines/some-pipeline",
        ).mock(
            return_value=httpx.Response(
                200, json=SAMPLE_PANDAS_RECORDS_INFERENCE_RESPONSE
            )
        )

        add_deployment_for_pipeline_responder(
            respx_mock,
            self.test_client.api_endpoint,
            deployment_id=1,
            deployment_name="some-pipeline",
        )
        add_deployment_by_id_responder(respx_mock, self.test_client.api_endpoint)
        output_df = await self.pipeline.parallel_infer(
            tensor=SAMPLE_PANDAS_RECORDS_JSON_PARALLEL_BATCH,
            batch_size=2,
            num_parallel=3,
        )
        assert isinstance(output_df, pd.DataFrame)
        assert 2 == len(output_df)

    @respx.mock
    @pytest.mark.asyncio()
    async def test_parallel_infer_with_pandas_df(self, respx_mock):
        respx.post(
            "http://engine-lb.some-pipeline-2:29502/pipelines/some-pipeline",
        ).mock(
            return_value=httpx.Response(
                200, json=SAMPLE_PANDAS_RECORDS_INFERENCE_RESPONSE
            )
        )

        add_deployment_for_pipeline_responder(
            respx_mock,
            self.test_client.api_endpoint,
            deployment_id=2,
            deployment_name="some-pipeline",
        )
        add_deployment_by_id_responder(
            respx_mock,
            self.test_client.api_endpoint,
            deployment_id=2,
            deployment_name="some-pipeline",
        )
        output_df = await self.pipeline.parallel_infer(
            tensor=SAMPLE_PANDAS_RECORDS_JSON, num_parallel=3
        )
        assert isinstance(output_df, pd.DataFrame)
        assert 3 == len(output_df)
        assert 5 == respx_mock.calls.call_count

    @pytest.mark.asyncio()
    async def test_split_result_and_error(self):
        infer_result_list = pd.read_pickle(
            open("unit_tests/outputs/parallel_infer_results_with_errors.pkl", "rb")
        )
        batch_mapping = [1, 1, 1, 1, 1]
        output_df = await self.pipeline._split_result_and_error(
            infer_result_list, batch_mapping
        )
        assert isinstance(output_df, pd.DataFrame)
        assert 2 == len(output_df[output_df["error"] == ""])
        assert 3 == len(output_df[output_df["error"] != ""])
