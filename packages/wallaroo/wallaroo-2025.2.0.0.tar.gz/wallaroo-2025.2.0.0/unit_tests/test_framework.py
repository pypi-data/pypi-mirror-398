import pydantic
import pytest

from wallaroo.engine_config import ModelOptimizationConfigError
from wallaroo.framework import CustomConfig, Framework, VLLMConfig


def test_custom_config_with_defaults():
    config = CustomConfig()
    assert config.framework == "custom"
    assert config.model_path == "./model/"
    result = config.to_dict()

    assert result == {
        "framework": "custom",
        "config": {"model_path": "./model/"},
    }


def test_custom_config_with_arbitrary_fields():
    config = CustomConfig(model_path="/some/path/to/model", some_field="some_value")
    assert config.some_field == "some_value"

    result = config.to_dict()
    assert result == {
        "framework": "custom",
        "config": {"model_path": "/some/path/to/model", "some_field": "some_value"},
    }


def test_vllm_config_with_defaults():
    config = VLLMConfig()
    assert config.framework == "vllm"

    result = config.to_dict()

    assert result == {
        "config": {
            "gpu_memory_utilization": 0.9,
            "kv_cache_dtype": "auto",
            "max_num_seqs": 256,
            "max_seq_len_to_capture": 8192,
            "quantization": "none",
        },
        "framework": "vllm",
    }


@pytest.mark.parametrize(
    "kv_cache_dtype, quantization, expected_kv_cache_dtype, expected_quantization",
    [
        ("fp8_e4m3", "compressed-tensors", "fp8_e4m3", "compressed-tensors"),
        ("mxint8", "mxfp6", "mxint8", "mxfp6"),
    ],
)
def test_vllm_config(
    kv_cache_dtype, quantization, expected_kv_cache_dtype, expected_quantization
):
    config = VLLMConfig(
        device_group=[0, 1],
        max_model_len=1024,
        max_num_seqs=2048,
        max_seq_len_to_capture=4096,
        gpu_memory_utilization=0.8,
        kv_cache_dtype=kv_cache_dtype,
        quantization=quantization,
        block_size=32,
    )

    assert config.framework == "vllm"

    result = config.to_dict()

    assert result == {
        "framework": "vllm",
        "config": {
            "device_group": [0, 1],
            "gpu_memory_utilization": 0.8,
            "kv_cache_dtype": expected_kv_cache_dtype,
            "max_model_len": 1024,
            "max_num_seqs": 2048,
            "max_seq_len_to_capture": 4096,
            "quantization": expected_quantization,
            "block_size": 32,
        },
    }


@pytest.mark.parametrize(
    "device_group, max_model_len, max_num_seqs, max_seq_len_to_capture, gpu_memory_utilization, kv_cache_dtype, quantization, block_size",
    [
        (
            [0, 1],
            -0.1,
            1024,
            4096,
            0.9,
            "auto",
            "none",
            None,
        ),
        (
            [0, 1],
            1.1,
            1024,
            4096,
            0.9,
            "auto",
            "none",
            None,
        ),
        (
            [0, 1],
            1024,
            1,
            4096,
            0.9,
            "invalid_dtype",
            "none",
            None,
        ),
        (
            [0, 1],
            1024,
            1,
            4096,
            0.9,
            "auto",
            "invalid_quant",
            None,
        ),
        (
            [0, 1],
            1.1,
            1,
            4096,
            0.9,
            "invalid_dtype",
            "invalid_quant",
            None,
        ),
        (
            [0, 1],
            1024,
            1,
            4096,
            0.9,
            "auto",
            "none",
            "not-an-int",
        ),
        (
            "not-a-list",
            1024,
            1,
            4096,
            0.9,
            "auto",
            "none",
            None,
        ),
        (
            ["not-a-list-of-ints"],
            1024,
            1,
            4096,
            0.9,
            "auto",
            "none",
            None,
        ),
    ],
)
def test_vllm_config_invalid_values(
    device_group,
    max_model_len,
    max_num_seqs,
    max_seq_len_to_capture,
    gpu_memory_utilization,
    kv_cache_dtype,
    quantization,
    block_size,
):
    with pytest.raises(pydantic.ValidationError):
        _ = VLLMConfig(
            device_group=device_group,
            max_model_len=max_model_len,
            max_num_seqs=max_num_seqs,
            max_seq_len_to_capture=max_seq_len_to_capture,
            gpu_memory_utilization=gpu_memory_utilization,
            kv_cache_dtype=kv_cache_dtype,
            quantization=quantization,
            block_size=block_size,
        )


@pytest.mark.parametrize(
    "framework, config",
    [
        (Framework.CUSTOM, CustomConfig()),
        (Framework.VLLM, VLLMConfig()),
        (Framework.KERAS, None),
    ],
)
def test_framework_validate(framework, config):
    framework.validate(config)


@pytest.mark.parametrize(
    "framework, config",
    [
        (Framework.CUSTOM, None),
        (Framework.CUSTOM, VLLMConfig()),
        (Framework.VLLM, None),
        (Framework.VLLM, CustomConfig()),
        (Framework.KERAS, VLLMConfig()),
        (Framework.KERAS, CustomConfig()),
    ],
)
def test_framework_validate_invalid_config(framework, config):
    with pytest.raises(
        ModelOptimizationConfigError,
        match="The specified model optimization configuration is not available. "
        "Please try this operation again using a different configuration "
        "or contact Wallaroo at support@wallaroo.ai for questions or help.",
    ):
        framework.validate(config)
