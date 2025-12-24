"""This module features utilities for compiling models using `qaic`."""

import logging
import time
from pathlib import Path
from typing import Any

from pydata_util.nats import CustomConfig, NATSMessage, QaicConfig, VLLMConfig

logger = logging.getLogger(__name__)


def compile_model(qeff_model: Any, qaic_config: QaicConfig) -> None:
    """Compile a model using `qaic`.

    :param qeff_model: `QEfficient` model to compile.
    :param qaic_config: `qaic` configuration.

    :return: Path to the generated QPC file.
    """

    logging.info("Compiling model to qaic...")
    start = time.time()

    # For more info check: https://quic.github.io/efficient-transformers/source/python_api.html#QEfficient.transformers.models.modeling_auto.QEFFAutoModelForCausalLM.compile
    generated_qpc_path: str = qeff_model.compile(**qaic_config.model_dump())

    elapsed = time.time() - start
    logging.debug(f"Saved QPC to `{generated_qpc_path}`.")
    logging.debug(f"Finished in {elapsed:.2f}s.")


def load_model(model_path: Path) -> Any:
    """Load a model using `QEfficient`.

    :param model_path: Path to the model to load.

    :return: Loaded model.
    """
    from QEfficient import QEFFAutoModelForCausalLM as AutoModelForCausalLM

    logging.debug(f"Loading model using `QEfficient` from `{model_path}`...")
    start = time.time()

    # For more info check: https://quic.github.io/efficient-transformers/source/python_api.html#QEfficient.transformers.models.modeling_auto.QEFFAutoModelForCausalLM
    qeff_model = AutoModelForCausalLM.from_pretrained(
        model_path.as_posix(),
        continuous_batching=True,  # Enable continuous batching mode, needed for using `full_batch_size`  # noqa: E501
    )

    elapsed = time.time() - start
    logging.debug(f"Model loaded in {elapsed:.2f}s.")

    return qeff_model


def load_and_compile(nats_message: NATSMessage) -> None:
    """Load a model using `QEfficient` and compile it using `qaic`.

    :param nats_message: NATS message.
    """
    _raise_error_if_invalid_framework_config(nats_message.model_framework_config)
    qaic_config: QaicConfig = _raise_error_if_not_qaic_config(nats_message.model_accel)
    model_path = _get_model_path(nats_message)

    qeff_model = load_model(model_path)
    compile_model(qeff_model, qaic_config)


def load_yaml(yaml_path: Path) -> dict:
    """Load a YAML file and return its contents as a dictionary.

    :param yaml_path: Path to the YAML file to load.

    :return: Contents of the YAML file as a dictionary.
    """
    import yaml

    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def _get_model_path(nats_message: NATSMessage) -> Path:
    """Get the path to the unzipped model.

    :param nats_message: NATS message.
    """
    return (
        nats_message.model_framework_config.model_path
        if isinstance(nats_message.model_framework_config, CustomConfig)
        else nats_message.model_file_name
    )


def _raise_error_if_invalid_framework_config(
    config: Any,
) -> None:
    """Validate that the provided `FrameworkConfig` maps to `Framework.CUSTOM`
    or `Framework.VLLM`.

    :param config: Configuration to validate.

    :raises ValueError: If the config is not a FrameworkConfig instance
    """

    if not isinstance(config, (CustomConfig, VLLMConfig)):
        raise ValueError(
            f"Expected `CustomConfig` or `VLLMConfig`, got `{type(config)}`"
        )


def _raise_error_if_not_qaic_config(config: Any) -> QaicConfig:
    """Validate that the provided config is a QaicConfig instance.

    :param config: Configuration to validate.
    :return: The validated QaicConfig instance.
    :raises ValueError: If the config is not a QaicConfig instance
    """
    if not isinstance(config, QaicConfig):
        raise ValueError(f"Expected `QaicConfig`, got `{type(config)}`")
    return config
