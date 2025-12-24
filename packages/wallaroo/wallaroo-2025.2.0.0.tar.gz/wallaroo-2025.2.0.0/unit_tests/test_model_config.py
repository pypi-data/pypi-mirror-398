import base64
import datetime

import httpx
import pyarrow as pa
import pytest
import respx

import wallaroo
from wallaroo.dynamic_batching_config import DynamicBatchingConfig
from wallaroo.model_config import ModelConfig

from . import testutil

input_schema = pa.schema(
    [
        pa.field("tensor_i", pa.fixed_shape_tensor(pa.float32(), [4, 4])),
    ]
)
input_schema_encoded = base64.b64encode(bytes(input_schema.serialize())).decode("utf8")


output_schema = pa.schema(
    [pa.field("tensor_o", pa.fixed_shape_tensor(pa.float32(), [4, 4]))]
)
output_schema_encoded = base64.b64encode(bytes(output_schema.serialize())).decode(
    "utf8"
)


class TestModelConfig:
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
        model_config = ModelConfig(
            client=self.test_client,
            data={
                "id": 1,
                "filter_threshold": 0.1234,
                "model": {
                    "id": 2,
                },
                "runtime": "onnx",
                "tensor_fields": ["foo", "bar", "baz"],
                "dynamic_batching_config": {
                    "max_batch_delay_ms": 10,
                    "batch_size_target": 4,
                    "batch_size_limit": 10,
                },
                "input_schema": input_schema_encoded,
                "output_schema": output_schema_encoded,
            },
        )

        assert 1 == model_config.id()
        assert 0.1234 == model_config.filter_threshold()
        assert 2 == model_config.model_version().id()
        assert "onnx" == model_config.runtime()
        assert ["foo", "bar", "baz"] == model_config.tensor_fields()
        assert isinstance(model_config.dynamic_batching_config(), DynamicBatchingConfig)
        assert 10 == model_config.dynamic_batching_config().max_batch_delay_ms
        assert input_schema_encoded == model_config.input_schema()
        assert output_schema_encoded == model_config.output_schema()

    @pytest.mark.parametrize(
        "method_name, want_value",
        [
            ("filter_threshold", 0.1234),
            ("runtime", "onnx"),
            ("tensor_fields", ["foo", "bar"]),
            ("dynamic_batching_config", None),
            ("input_schema", input_schema_encoded),
            ("output_schema", output_schema_encoded),
        ],
    )
    @respx.mock(assert_all_mocked=False)
    def test_rehydrate(
        self,
        method_name,
        want_value,
        respx_mock,
    ):
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
                            "tensor_fields": ["foo", "bar"],
                            "dynamic_batching_config": None,
                            "input_schema": input_schema_encoded,
                            "output_schema": output_schema_encoded,
                        },
                    },
                },
            )
        )

        model_config = ModelConfig(client=self.test_client, data={"id": 1})

        assert want_value == getattr(model_config, method_name)()
        assert 1 == len(respx_mock.calls)
        # Another call to the same accessor shouldn't trigger any
        # additional GraphQL queries.
        assert want_value == getattr(model_config, method_name)()
        assert 1 == len(respx_mock.calls)
