import pytest

from wallaroo.dynamic_batching_config import DynamicBatchingConfig


class TestDynamicBatchingConfig:
    def setup_method(self):
        self.config_dict = {
            "max_batch_delay_ms": 10,
            "batch_size_target": 4,
            "batch_size_limit": 5,
        }
        self.config = DynamicBatchingConfig(**self.config_dict)

    def test_init(self):
        assert self.config.max_batch_delay_ms == self.config_dict["max_batch_delay_ms"]
        assert self.config.batch_size_target == self.config_dict["batch_size_target"]
        assert self.config.batch_size_limit == self.config_dict["batch_size_limit"]

    @pytest.mark.parametrize(
        "config_dict",
        [
            {"max_batch_delay_ms": "10", "batch_size_target": 4, "batch_size_limit": 5},
            {"max_batch_delay_ms": 10, "batch_size_target": "4", "batch_size_limit": 5},
            {"max_batch_delay_ms": 10, "batch_size_target": 4, "batch_size_limit": "5"},
        ],
    )
    def test_init_wrong_type(self, config_dict):
        with pytest.raises(ValueError):
            DynamicBatchingConfig(**config_dict)

    def test_init_set_wrong_type(self):
        dynamic_batching_config = DynamicBatchingConfig()
        with pytest.raises(ValueError):
            dynamic_batching_config.max_batch_delay_ms = "hello"

    def test_init_batch_size_limit_none(self):
        dynamic_batching_config = DynamicBatchingConfig(
            max_batch_delay_ms=10, batch_size_target=4
        )
        assert dynamic_batching_config.batch_size_limit is None

    def test_from_dict(self):
        config_from_dict = DynamicBatchingConfig.from_dict(self.config_dict)
        assert (
            config_from_dict.max_batch_delay_ms
            == self.config_dict["max_batch_delay_ms"]
        )
        assert (
            config_from_dict.batch_size_target == self.config_dict["batch_size_target"]
        )
        assert config_from_dict.batch_size_limit == self.config_dict["batch_size_limit"]

    @pytest.mark.parametrize(
        "config_dict",
        [
            {"max_batch_delay_ms": None, "batch_size_target": 4, "batch_size_limit": 5},
            {"max_batch_delay_ms": 10, "batch_size_target": "4", "batch_size_limit": 5},
        ],
    )
    def test_from_dict_wrong_type(self, config_dict):
        with pytest.raises(ValueError):
            DynamicBatchingConfig.from_dict(config_dict)

    def test_to_json(self):
        config_json = self.config.to_json()
        assert isinstance(config_json, dict)
