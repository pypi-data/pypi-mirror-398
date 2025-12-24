# test_continuous_batching_config.py
import pytest
from pydantic import ValidationError

from wallaroo.continuous_batching_config import ContinuousBatchingConfig


@pytest.mark.parametrize(
    "max_concurrent_batch_size, expected",
    [
        (None, 1),  # Test default batch size
        (5, 5),  # Test valid batch size
    ],
)
def test_valid_max_concurrent_batch_size(max_concurrent_batch_size, expected):
    if max_concurrent_batch_size is None:
        config = ContinuousBatchingConfig()
    else:
        config = ContinuousBatchingConfig(
            max_concurrent_batch_size=max_concurrent_batch_size
        )
    assert config.max_concurrent_batch_size == expected


@pytest.mark.parametrize(
    "invalid_value",
    [
        0,  # Test invalid value: zero
        -1,  # Test invalid value: negative
    ],
)
def test_invalid_max_concurrent_batch_size(invalid_value):
    with pytest.raises(ValidationError):
        ContinuousBatchingConfig(max_concurrent_batch_size=invalid_value)
