import datetime

import httpx
import respx

import wallaroo
from wallaroo.tag import Tag

from . import testutil


class TestTag:
    def setup_method(self):
        self.now = datetime.datetime.now()
        self.gql_client = testutil.new_gql_client(endpoint="http://api-lb/v1/graphql")
        self.test_client = wallaroo.Client(
            gql_client=self.gql_client,
            auth_type="test_auth",
            api_endpoint="http://api-lb:8080",
            config={"default_arch": "x86"},
        )

    def test_init_full_dict(self):
        tag = Tag(
            client=self.test_client,
            data={"id": 1, "tag": "test-tag"},
        )

        assert 1 == tag.id()
        assert "test-tag" == tag.tag()

    @respx.mock(assert_all_mocked=True)
    def test_rehydrate(self, respx_mock):
        respx_mock.post(
            "http://api-lb/v1/graphql",
            content__contains="query {}".format("TagById"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "tag_by_pk": {
                            "id": 9999,
                            "tag": "test-tag",
                        }
                    },
                },
            ),
        )

        tag = Tag(client=self.test_client, data={"id": 9999})
        assert tag.tag() == "test-tag"

    @respx.mock(assert_all_mocked=True)
    def test_client_create(self, respx_mock):
        respx_mock.post(
            "http://api-lb/v1/graphql",
            content__contains="mutation {}".format("CreateTag"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "insert_tag": {"returning": [{"id": 4, "tag": "hello-tag"}]}
                    }
                },
            ),
        )

        res = self.test_client.create_tag("hello-tag")
        assert isinstance(res, Tag)
        assert res.tag() == "hello-tag"

    @respx.mock(assert_all_mocked=True)
    def test_add_to_model(self, respx_mock):
        model_id = 1111
        tag_id = 9999

        variables = {"model_id": model_id, "tag_id": tag_id}
        respx_mock.post(
            "http://api-lb/v1/graphql",
            content__contains="mutation {}".format("AddTagToModel"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "insert_model_tag": {
                            "returning": [
                                variables,
                            ]
                        }
                    }
                },
            ),
        )
        tag = Tag(client=self.test_client, data={"id": tag_id, "tag": "test-tag"})

        res = tag.add_to_model(model_id)

        assert res["tag_id"] == tag_id
        assert res["model_id"] == model_id

    @respx.mock(assert_all_mocked=True)
    def test_remove_from_model(self, respx_mock):
        model_id = 1111
        tag_id = 9999
        respx_mock.post(
            "http://api-lb/v1/graphql",
            content__contains="mutation RemoveTagFromModel",
            json__variables__model_id=model_id,
            json__variables__tag_id=tag_id,
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "delete_model_tag": {
                            "returning": [
                                {
                                    "model_id": model_id,
                                    "tag_id": tag_id,
                                },
                            ]
                        }
                    }
                },
            ),
        )

        tag = Tag(client=self.test_client, data={"id": tag_id, "tag": "test-tag"})

        res = tag.remove_from_model(model_id)
        assert res["tag_id"] == tag_id
        assert res["model_id"] == model_id

    @respx.mock(assert_all_mocked=True)
    def test_add_to_pipeline(self, respx_mock):
        pipeline_id = 1111
        tag_id = 9999
        respx_mock.post(
            "http://api-lb/v1/graphql",
            content__contains="mutation AddTagToPipeline",
            json__variables__pipeline_id=pipeline_id,
            json__variables__tag_id=tag_id,
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "insert_pipeline_tag": {
                            "returning": [
                                {"tag_pk_id": tag_id, "pipeline_pk_id": pipeline_id},
                            ]
                        }
                    }
                },
            ),
        )

        tag = Tag(client=self.test_client, data={"id": 9999, "tag": "test-tag"})

        res = tag.add_to_pipeline(1111)
        assert res["tag_pk_id"] == tag_id
        assert res["pipeline_pk_id"] == pipeline_id

    @respx.mock(assert_all_mocked=True)
    def test_remove_from_pipeline(self, respx_mock):
        pipeline_id = 1111
        tag_id = 9999
        respx_mock.post(
            "http://api-lb/v1/graphql",
            content__contains="mutation RemoveTagFromPipeline",
            json__variables__pipeline_id=pipeline_id,
            json__variables__tag_id=tag_id,
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "delete_pipeline_tag": {
                            "returning": [
                                {
                                    "pipeline_pk_id": pipeline_id,
                                    "tag_pk_id": tag_id,
                                },
                            ]
                        }
                    }
                },
            ),
        )

        tag = Tag(client=self.test_client, data={"id": 9999, "tag": "test-tag"})

        res = tag.remove_from_pipeline(1111)
        assert res["tag_pk_id"] == tag_id
        assert res["pipeline_pk_id"] == pipeline_id
