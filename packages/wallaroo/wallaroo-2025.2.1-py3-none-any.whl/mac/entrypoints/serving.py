"""This module features entrypoints for serving a PythonStep using a Service."""

import logging
from pathlib import Path
from typing import Callable, Dict

from pydata_util.nats import NATSMessage
from pydata_util.nats.framework_config import CustomConfig
from pydata_util.types import SupportedFrameworks

from mac.config.python_step import (
    AutoInferenceConfig,
    CustomStepConfig,
    PythonStepConfig,
)
from mac.config.service import ServerConfig, ServiceConfig
from mac.config.service.creation import ServiceConfigFactory
from mac.inference.creation import InferenceBuilder
from mac.io.custom_step_loaders import load_custom_inference, load_custom_step
from mac.service.creation import ServiceFactory
from mac.types import (
    PythonStep,
    SupportedServices,
)

logger = logging.getLogger(__name__)


CUSTOM_STEP_LOADERS: Dict[SupportedFrameworks, Callable[..., PythonStep]] = {
    SupportedFrameworks.CUSTOM: load_custom_inference,
    SupportedFrameworks.PYTHON: load_custom_step,
}


def create_auto_inference_config(
    nats_message: NATSMessage,
) -> AutoInferenceConfig:
    """Creates an `AutoInferenceConfig` from a given `NATSMessage`.

    :param nats_message: A `NATSMessage` instance.

    :raises pydantic.ValidationError: If `AutoInferenceConfig` is invalid,
    then a `pydantic.ValidationError` is raised.

    :return: An `AutoInferenceConfig` instance.
    """
    return AutoInferenceConfig(
        framework=nats_message.model_framework, model_path=nats_message.model_file_name
    )


def create_custom_step_config(nats_message: NATSMessage) -> CustomStepConfig:
    """Creates an `CustomStepConfig` from a given `NATSMessage`.

    :param nats_message: A `NATSMessage` instance.

    :raises pydantic.ValidationError: If `CustomStepConfig` is invalid,
    then a `pydantic.ValidationError` is raised.

    :return: A `CustomStepConfig` instance.
    """
    return CustomStepConfig(
        framework=nats_message.model_framework,
        model_path=nats_message.model_file_name,
        modules_to_include=set([Path("*.py")]),
    )


def serve_auto_inference_from_nats_message(
    nats_message: NATSMessage,
    inference_builder: InferenceBuilder,
    inference_config_creator: Callable[
        [NATSMessage], AutoInferenceConfig
    ] = create_auto_inference_config,
    service_type: SupportedServices = SupportedServices.FLIGHT,
    host: str = "0.0.0.0",
    port: int = 8080,
) -> None:
    """Entrypoint for serving a `PythonStep` associated with an auto
    Inference from a given `NATSMessage`.

    :param nats_message: A `NATSMessage` instance.
    :param inference_builder: An `InferenceBuilder` instance.
    :param service_type: The `Service` to be used for serving the auto Inference.
    :param host: The service host.
    :param port: The service port.
    """
    logger.info(
        f"Serving auto Inference with `{service_type.value}` from `NATSMessage`..."
    )

    auto_inference_config = inference_config_creator(nats_message)
    service_config_kwargs = _get_service_config_kwargs(
        nats_message,
        service_type,
        auto_inference_config,
        host,
        port,
    )
    service_config = ServiceConfigFactory().create(
        service_type.value, **service_config_kwargs
    )
    auto_inference = inference_builder.create(auto_inference_config)

    serve_python_step(
        service_config=service_config,
        python_step=auto_inference.predict,
    )

    logger.info("Serving successful.")


def serve_custom_step_from_nats_message(
    nats_message: NATSMessage,
    service_type: SupportedServices = SupportedServices.FLIGHT,
    host: str = "0.0.0.0",
    port: int = 8080,
) -> None:
    """Entrypoint for serving a custom `PythonStep` (i.e. a custom Inference or
    a pre/post-processing step) from a given `NATSMessage`.

    :param nats_message: A `NATSMessage` instance.
    :param service_type: The `Service` to be used for serving the custom `PythonStep`.
    :param host: The service host.
    :param port: The service port.

    :raises ValueError: If the framework is not supported.
    """
    logger.info(
        f"Serving custom PythonStep with {service_type.value} from `NATSMessage`..."
    )

    custom_step_config = create_custom_step_config(nats_message=nats_message)
    service_config_kwargs = _get_service_config_kwargs(
        nats_message,
        service_type,
        custom_step_config,
        host,
        port,
    )
    service_config = ServiceConfigFactory().create(
        service_type.value, **service_config_kwargs
    )

    python_step = _get_python_step(
        nats_message=nats_message, custom_step_config=custom_step_config
    )

    serve_python_step(
        service_config=service_config,
        python_step=python_step,
    )

    logger.info("Serving successful.")


def serve_python_step(
    service_config: ServiceConfig,
    python_step: PythonStep,
) -> None:
    """Serve a `PythonStep` given a `ServiceConfig`.

    :param service_config: A `ServiceConfig` instance.
    :param python_step: A `PythonStep` instance.
    """
    service = ServiceFactory().create(
        service_config.service_type.value,
        config=service_config,
        python_step=python_step,
    )
    service.serve()


def _get_python_step(
    nats_message: NATSMessage, custom_step_config: CustomStepConfig
) -> PythonStep:
    """Returns a `PythonStep` instance based on the given `NATSMessage`.

    :param nats_message: A `NATSMessage` instance.

    :raises ValueError: If the framework is not supported.

    :return: A `PythonStep` instance.
    """
    match nats_message.model_framework:
        case SupportedFrameworks.CUSTOM:
            # For this case we need to pass `CustomConfig` that's included
            # in `NATSMessage` to `InferenceBuilder`
            custom_config = _get_custom_config(nats_message=nats_message)
            return _get_custom_step_loader(framework=nats_message.model_framework)(
                custom_step_config, custom_config
            )
        case SupportedFrameworks.PYTHON:
            return _get_custom_step_loader(framework=nats_message.model_framework)(
                custom_step_config
            )
        case _:
            raise ValueError(f"Unsupported framework: {nats_message.model_framework}")


def _get_custom_config(nats_message: NATSMessage) -> CustomConfig:
    """Returns the `CustomConfig` from a given `NATSMessage`.

    :param nats_message: A `NATSMessage` instance.

    :return: The custom config.

    :raises ValueError: If the framework config is not of type `CustomConfig`.
    """
    config = nats_message.model_framework_config
    if not isinstance(config, CustomConfig):
        raise ValueError("Custom config is not of type `CustomConfig`")

    return config


def _get_custom_step_loader(
    framework: SupportedFrameworks,
) -> Callable[..., PythonStep]:
    """Returns the custom `PythonStep` loader for the given framework.

    :param framework: The framework to get the custom `PythonStep` loader for.

    :raises ValueError: If the framework is not supported.

    :return: The custom step loader for the given framework.
    """
    try:
        return CUSTOM_STEP_LOADERS[framework]
    except KeyError:
        raise ValueError(f"Unsupported framework: {framework}")


def _get_service_config_kwargs(
    nats_message: NATSMessage,
    service_type: SupportedServices,
    python_step_config: PythonStepConfig,
    host: str,
    port: int,
) -> dict:
    """Returns the service config kwargs.

    :param nats_message: The `NATSMessage` instance.
    :param service_type: The service type.
    :param python_step_config: The `PythonStepConfig` instance.
    :param host: The service host.
    :param port: The service port.

    :return: The service config kwargs.
    """
    kwargs = {
        "python_step": python_step_config,
        "server": ServerConfig(host=host, port=port),
    }

    if service_type.value == "flight":
        kwargs["output_schema"] = nats_message.model_output_schema

    return kwargs
