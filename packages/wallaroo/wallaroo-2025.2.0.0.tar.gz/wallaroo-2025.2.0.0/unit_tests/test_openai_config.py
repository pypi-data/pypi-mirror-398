import pytest

from wallaroo.openai_config import OpenaiConfig


def test_openai_config_default_values():
    """Test that OpenaiConfig has correct default values"""
    config = OpenaiConfig()
    assert config.enabled is False
    assert config.completion_config == {}
    assert config.chat_completion_config == {}


def test_openai_config_custom_values():
    """Test that OpenaiConfig can be initialized with custom values"""
    completion_config = {"model": "gpt-3.5-turbo", "temperature": 0.7}
    chat_completion_config = {"model": "gpt-4", "max_tokens": 100}

    config = OpenaiConfig(
        enabled=True,
        completion_config=completion_config,
        chat_completion_config=chat_completion_config,
    )

    assert config.enabled is True
    assert config.completion_config == completion_config
    assert config.chat_completion_config == chat_completion_config


@pytest.mark.parametrize(
    "invalid_config",
    [
        {"enabled": "not-a-boolean"},  # Invalid type for enabled
        {"completion_config": "not-a-dict"},  # Invalid type for completion_config
        {
            "chat_completion_config": "not-a-dict"
        },  # Invalid type for chat_completion_config
    ],
)
def test_openai_config_validation(invalid_config):
    """Test that OpenaiConfig validates input types correctly"""
    with pytest.raises(ValueError):
        OpenaiConfig(**invalid_config)
