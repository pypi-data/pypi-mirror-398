import datetime

import httpx
import respx

import wallaroo
from wallaroo.comment import Comment

from . import testutil


class TestComment:
    def setup_method(self):
        self.now = datetime.datetime.now()
        self.gql_client = testutil.new_gql_client(endpoint="http://api-lb/v1/graphql")
        self.test_client = wallaroo.Client(
            gql_client=self.gql_client,
            auth_type="test_auth",
            api_endpoint="http://api-lb",
            config={"default_arch": "x86"},
        )

    def test_init_full_dict(self):
        comment = Comment(
            client=self.test_client,
            data={
                "id": 1,
                "user_id": "AAAA-BBBB-CCCC-DDDD",
                "message": "Comment Message",
            },
        )

        assert 1 == comment.id()
        assert "AAAA-BBBB-CCCC-DDDD" == str(comment.user_id())
        assert "Comment Message" == str(comment.message())

    @respx.mock(assert_all_mocked=False)
    def test_rehydrate(self, respx_mock):
        comment = Comment(
            client=self.test_client,
            data={
                "id": 9999,
                "user_id": "AAAA-BBBB-CCCC-DDDD",
                "message": "Comment Message",
                "updated_at": self.now.isoformat(),
            },
        )
        assert 9999 == comment.id()
        assert "AAAA-BBBB-CCCC-DDDD" == comment.user_id()
        assert "Comment Message" == comment.message()
        # self.assertEqual(self.now.isoformat(), comment.updated_at())

    @respx.mock(assert_all_mocked=False)
    def test_add_to_model(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="mutation {}".format("AddCommentToModel"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "insert_model_variant_comment": {
                            "returning": [
                                {"comment_id": 9999, "model_pk_id": 1111},
                            ]
                        }
                    }
                },
            ),
        )

        comment = Comment(
            client=self.test_client,
            data={"id": 8888, "comment_id": 9999, "model_pk_id": 1111},
        )

        res = comment.add_to_model(1111)

        assert res["comment_id"] == 9999
        assert res["model_pk_id"] == 1111

    @respx.mock(assert_all_mocked=False)
    def test_remove_from_model(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="mutation {}".format("RemoveCommentFromModel"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "delete_model_variant_comment": {
                            "returning": [
                                {
                                    "model_id": 1111,
                                    "comment_id": 9999,
                                },
                            ]
                        }
                    }
                },
            ),
        )

        comment = Comment(
            client=self.test_client,
            data={"id": 8888, "comment_id": 9999, "model_id": 1111},
        )

        comment.remove_from_model(1111)

    @respx.mock(assert_all_mocked=False)
    def test_add_to_pipeline(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="mutation {}".format("AddCommentToPipeline"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "insert_pipeline_comment": {
                            "returning": [
                                {"comment_id": 9999, "pipeline_pk_id": 1111},
                            ]
                        }
                    }
                },
            ),
        )

        comment = Comment(
            client=self.test_client,
            data={"id": 1, "comment_id": 9999, "pipeline_pk_id": 1111},
        )

        res = comment.add_to_pipeline(1111)
        assert res["comment_id"] == 9999
        assert res["pipeline_pk_id"] == 1111

    @respx.mock(assert_all_mocked=False)
    def test_remove_from_pipeline(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="mutation {}".format("RemoveCommentFromPipeline"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "delete_pipeline_comment": {
                            "returning": [
                                {
                                    "pipeline_pk_id": 1111,
                                    "comment_pk_id": 9999,
                                },
                            ]
                        }
                    }
                },
            ),
        )

        comment = Comment(
            client=self.test_client,
            data={"id": 1, "comment_id": 9999, "pipeline_pk_id": 1111},
        )

        comment.remove_from_pipeline(1111)

    @respx.mock(assert_all_mocked=False)
    def test_list_model_versions(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("ModelsForComment"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "comment_by_pk": {
                            "model_variant_comments": [
                                {
                                    "model": {
                                        "id": 1,
                                        "file_name": "1.1",
                                        "model_id": "1",
                                        "sha": "SHA",
                                        "owner_id": "AAA-BBB",
                                        "visibility": "private",
                                        "updated_at": "2022-02-01T19:47:17.991567+00:00",
                                    }
                                }
                            ]
                        }
                    }
                },
            ),
        )

        comment = Comment(
            client=self.test_client,
            data={"id": 1, "comment_id": 9999, "pipeline_pk_id": 1111},
        )

        the_model = comment.list_model_versions()[0]

        assert 1 == the_model.id()

    @respx.mock(assert_all_mocked=False)
    def test_list_pipelines(self, respx_mock):
        respx_mock.post(
            f"{self.test_client.api_endpoint}/v1/graphql",
            content__contains="query {}".format("PipelinesForComment"),
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "comment_by_pk": {
                            "pipeline_comments": [
                                {
                                    "pipeline": {
                                        "id": 1,
                                        "owner_id": "AAAA-BBBB-CCCC-DDDD",
                                        "updated_at": "2022-02-01T20:05:26.024056+00:00",
                                        "visibility": "private",
                                    }
                                }
                            ]
                        }
                    }
                },
            ),
        )

        comment = Comment(
            client=self.test_client,
            data={"id": 1, "comment_id": 9999, "pipeline_pk_id": 1111},
        )

        the_pipeline = comment.list_pipelines()[0]

        assert 1 == the_pipeline.id()
        assert "AAAA-BBBB-CCCC-DDDD" == the_pipeline.owner_id()
