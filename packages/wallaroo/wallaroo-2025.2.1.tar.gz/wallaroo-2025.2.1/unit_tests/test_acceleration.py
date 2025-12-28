import pydantic
import pytest

from wallaroo.engine_config import (
    Acceleration,
    ModelOptimizationConfigError,
    QaicConfig,
    QaicWithConfig,
)


def test_qaic_config_init_defaults():
    config = QaicConfig()

    assert config.num_cores == 16
    assert config.num_devices == 1
    assert config.ctx_len == 128
    assert config.prefill_seq_len == 32
    assert config.full_batch_size == 8
    assert config.mxfp6_matmul is False
    assert config.mxint8_kv_cache is False
    assert config.aic_enable_depth_first is False


def test_qaic_config_init():
    config = QaicConfig(
        num_cores=16,
        aic_enable_depth_first=True,
        ctx_len=2048,
        prefill_seq_len=128,
        num_devices=4,
        full_batch_size=16,
        mxfp6_matmul=True,
        mxint8_kv_cache=True,
    )

    assert config.num_cores == 16
    assert config.num_devices == 4
    assert config.ctx_len == 2048
    assert config.prefill_seq_len == 128
    assert config.full_batch_size == 16
    assert config.mxfp6_matmul is True
    assert config.mxint8_kv_cache is True


@pytest.mark.parametrize(
    "num_cores, num_devices, ctx_len, prefill_seq_len, full_batch_size, mxfp6_matmul, mxint8_kv_cache, aic_enable_depth_first",
    [
        (
            0,
            1,
            128,
            32,
            None,
            True,
            False,
            False,
        ),
        (
            "some-string",
            1,
            128,
            32,
            None,
            True,
            False,
            False,
        ),
        (
            14,
            0,
            128,
            32,
            None,
            True,
            False,
            False,
        ),
        (
            14,
            "some-string",
            128,
            32,
            None,
            True,
            False,
            False,
        ),
        (
            14,
            1,
            0,
            32,
            None,
            True,
            False,
            False,
        ),
        (
            14,
            1,
            "some-string",
            32,
            None,
            True,
            False,
            False,
        ),
        (
            14,
            1,
            128,
            0,
            None,
            True,
            False,
            False,
        ),
        (
            14,
            1,
            128,
            "some-string",
            None,
            True,
            False,
            False,
        ),
        (
            14,
            1,
            128,
            16,
            0,
            True,
            False,
            False,
        ),
        (
            14,
            1,
            128,
            16,
            "some-string",
            True,
            False,
            False,
        ),
        (
            14,
            1,
            128,
            16,
            16,
            "some-string",
            False,
            False,
        ),
        (
            14,
            1,
            128,
            16,
            16,
            True,
            "some-string",
            False,
        ),
        (
            14,
            1,
            128,
            16,
            16,
            True,
            False,
            "some-string",
        ),
    ],
)
def test_qaic_config_invalid_values(
    num_cores,
    num_devices,
    ctx_len,
    prefill_seq_len,
    full_batch_size,
    mxfp6_matmul,
    mxint8_kv_cache,
    aic_enable_depth_first,
):
    with pytest.raises(pydantic.ValidationError):
        _ = QaicConfig(
            num_cores=num_cores,
            num_devices=num_devices,
            ctx_len=ctx_len,
            prefill_seq_len=prefill_seq_len,
            full_batch_size=full_batch_size,
            mxfp6_matmul=mxfp6_matmul,
            mxint8_kv_cache=mxint8_kv_cache,
            aic_enable_depth_first=aic_enable_depth_first,
        )


def test_create_acceleration_with_config():
    accel_with_config = Acceleration.QAIC.with_config(QaicConfig())
    assert isinstance(accel_with_config, QaicWithConfig)
    assert accel_with_config.accel == Acceleration.QAIC
    assert accel_with_config.config == QaicConfig()


@pytest.mark.parametrize(
    "acceleration",
    [
        Acceleration._None,
        Acceleration.CUDA,
        Acceleration.Jetson,
        Acceleration.OpenVINO,
        Acceleration.QAIC,
    ],
)
def test_create_acceleration_with_config_raise_error(acceleration):
    with pytest.raises(
        ModelOptimizationConfigError,
        match="The specified model optimization configuration is not available. "
        "Please try this operation again using a different configuration "
        "or contact Wallaroo at support@wallaroo.ai for questions or help.",
    ):
        acceleration.with_config("not-a-valid-config")


def test_qaic_with_config_init():
    accel_with_config = QaicWithConfig(config=QaicConfig())
    assert isinstance(accel_with_config, QaicWithConfig)
    assert accel_with_config.accel == Acceleration.QAIC
    assert accel_with_config.config == QaicConfig()


def test_qaic_with_config_init_defaults():
    accel_with_config = QaicWithConfig()
    assert isinstance(accel_with_config, QaicWithConfig)
    assert accel_with_config.accel == Acceleration.QAIC
    assert accel_with_config.config.model_dump(
        exclude_unset=True
    ) == QaicConfig().model_dump(exclude_unset=True)


def test_qaic_with_config_to_dict():
    accel_with_config = QaicWithConfig()
    assert isinstance(accel_with_config, QaicWithConfig)
    assert accel_with_config.to_dict() == {
        "qaic": {
            "aic_enable_depth_first": False,
            "ctx_len": 128,
            "num_devices": 1,
            "mxfp6_matmul": False,
            "mxint8_kv_cache": False,
            "num_cores": 16,
            "prefill_seq_len": 32,
            "full_batch_size": 8,
        }
    }
