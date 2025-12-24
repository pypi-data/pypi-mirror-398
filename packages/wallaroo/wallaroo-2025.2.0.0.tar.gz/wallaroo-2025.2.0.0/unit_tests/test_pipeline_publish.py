import pytest
from io import StringIO
from unittest import mock

import httpx
import unittest

from wallaroo.engine_config import EngineConfig
from wallaroo.pipeline_publish import PipelinePublish
from wallaroo.wallaroo_ml_ops_api_client.models import PipelinePublishStatus
from . import testutil
import respx

import wallaroo


class TestPipelinePublish:

    def setup_method(self):
        self.gql_client = testutil.new_gql_client(
            endpoint="http://api-lb:8080/v1/graphql",
        )
        self.test_client = wallaroo.Client(
            gql_client=self.gql_client,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )
        self.pipeline_publish = PipelinePublish(
            client=self.test_client,
            id=123,
            status=None,
            created_at="2022-03-02T08:13:38.627443",
            engine_config=EngineConfig(
                cpus=1,
            ),
            pipeline_version_id=1,
            user_images=None,
            updated_at="2022-03-02T08:13:38.627443",
        )

    @staticmethod
    def add_pipeline_publish_resp(status):
        return {
            "id": 123,
            "status": status,
            "created_at": "2022-03-02T08:13:38.627443",
            "updated_at": "2022-03-02T08:13:38.627443",
            "pipeline_version_id": 1,
            "pipeline_name": "test-pipeline",
            "engine_config": {
                "engine": {},
                "enginelb": {},
                "engineAux": {"images": {}},
                "node_selector": {},
            },
            "user_images": None,
            "docker_run_variables": {},
            "replaces": [],
            "created_on_version": "2024.1.0",
        }

    @respx.mock(assert_all_mocked=True)
    def test_wait_for_status_published(self, respx_mock):
        # Mock the necessary dependencies
        get_pipeline_publish_resp = self.add_pipeline_publish_resp(PipelinePublishStatus.PUBLISHED)

        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/pipelines/get_publish_status").mock(
            return_value=httpx.Response(200, json=get_pipeline_publish_resp)
        )
        # Call the method under test
        with mock.patch("sys.stdout", new_callable=StringIO) as f:
            result = self.pipeline_publish._wait_for_status()
            res = f.getvalue()
        # Assert the expected result
        expected_string = "Waiting for pipeline publish... It may take up to 600 sec.\n" \
                          "Pipeline is publishing. Published.\n"
        assert expected_string == res
        assert result.status == PipelinePublishStatus.PUBLISHED

    @respx.mock(assert_all_mocked=True)
    def test_wait_for_status_publishing(self, respx_mock):
        # Mock the necessary dependencies
        get_pipeline_publish_resp_1 = self.add_pipeline_publish_resp(PipelinePublishStatus.PENDINGPUBLISH)
        get_pipeline_publish_resp_2 = self.add_pipeline_publish_resp(PipelinePublishStatus.PUBLISHED)

        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/pipelines/get_publish_status").mock(
            side_effect=[httpx.Response(200, json=get_pipeline_publish_resp_1),
                         httpx.Response(200, json=get_pipeline_publish_resp_2)]
        )
        with mock.patch("sys.stdout", new_callable=StringIO) as f:
            result = self.pipeline_publish._wait_for_status()
            res = f.getvalue()

        # Assert the expected result
        expected_string = "Waiting for pipeline publish... It may take up to 600 sec.\n" \
                          "Pipeline is publishing.. Published.\n"
        assert expected_string == res
        assert result.status == PipelinePublishStatus.PUBLISHED

    @respx.mock(assert_all_mocked=True)
    def test_wait_for_status_error(self, respx_mock):
        # Mock the necessary dependencies
        get_pipeline_publish_resp = self.add_pipeline_publish_resp(PipelinePublishStatus.ERROR)
        get_pipeline_publish_resp["error"] = "Error message"
        respx_mock.post(f"{self.test_client.api_endpoint}/v1/api/pipelines/get_publish_status").mock(
            return_value=httpx.Response(200, json=get_pipeline_publish_resp)
        )
        # Assert the expected result
        expected_string = "Waiting for pipeline publish... It may take up to 600 sec.\n" \
                          "Pipeline is publishing. ERROR. Error message\n"

        with pytest.raises(Exception):
            with mock.patch("sys.stderr", new_callable=StringIO) as f:
                result = self.pipeline_publish._wait_for_status()
                res = f.getvalue()

            assert result.status == PipelinePublishStatus.ERROR
            assert expected_string == res
