"""This module features the CLI for serving a custom PythonStep."""

import logging
from pathlib import Path

import typer
from pydata_util.nats import (
    parse_nats_message_from_model_json,
)
from pydata_util.types import SupportedFrameworks, SupportedNATSMessages

from mac.entrypoints.serving import serve_custom_step_from_nats_message
from mac.types import SupportedServices

app = typer.Typer()


logger = logging.getLogger(__name__)


def _exit_with_error(message: str, title: str = "Error") -> None:
    """Exit with error code 1 and consistent error formatting.

    Note: The "Error:" prefix is important as mkenv depends on this keying
    to form error_summary from the logs.
    """
    typer.echo(
        typer.style(
            f"\n{title}!",
            fg=typer.colors.RED,
            bold=True,
        )
    )
    typer.echo(
        typer.style(
            f"Error: {message}",
            fg=typer.colors.RED,
        )
    )
    raise typer.Exit(code=1)


@app.command()
def serve(
    config_path: Path = typer.Option(..., "--config-path", exists=True),
    service: SupportedServices = SupportedServices.FLIGHT,
    host: str = "0.0.0.0",
    port: int = 8080,
):
    """Serve a custom PythonStep with a specified service.

    :param config_path: Path to the JSON config file.
    :param service: Service to use for serving the PythonStep.
    :param host: Host to serve the PythonStep on.
    :param port: Port to serve the PythonStep on.
    """
    nats_message = parse_nats_message_from_model_json(
        file_path=config_path,
        message_type=SupportedNATSMessages.PACKAGING,
    )
    logger.debug(f"Parsed NATS message: {nats_message}")
    serve_custom_step_from_nats_message(
        nats_message=nats_message, service_type=service, host=host, port=port
    )


@app.command()
def compile_qaic(
    config_path: Path = typer.Option(..., "--config-path", exists=True),
) -> None:
    """Export and compile model to qaic.

    :param config_path: Path to the JSON config file.
    """
    from mac.qaic_utils import load_and_compile

    nats_message = parse_nats_message_from_model_json(
        file_path=config_path,
        message_type=SupportedNATSMessages.PACKAGING,
    )
    logger.debug(f"Parsed NATS message: {nats_message}")

    load_and_compile(nats_message)


@app.command()
def validate_custom(
    config_path: Path = typer.Option(..., "--config-path", exists=True),
):
    """Validate a custom (BYOP) model structure.

    This command checks if a BYOP model follows the required structure:
    1. Contains an Inference-inherited class
    2. Contains an InferenceBuilder-inherited class
    3. The Inference class has a predict method
    4. The Inference class has the expected_model_types property

    :param config_path: Path to the JSON config file.
    """
    from mac.validation import BYOPValidationError, validate_byop_structure

    nats_message = parse_nats_message_from_model_json(
        file_path=config_path,
        message_type=SupportedNATSMessages.PACKAGING,
    )
    logger.debug(f"Parsed NATS message: {nats_message}")

    if nats_message.model_framework != SupportedFrameworks.CUSTOM:
        _exit_with_error(
            f"Model framework is '{nats_message.model_framework.value}', "
            "but validation is only for 'custom' (BYOP) models.",
            "Invalid Framework",
        )

    model_path = nats_message.model_file_name

    typer.echo(
        typer.style(
            f"Validating BYOP model at: {model_path}",
            fg=typer.colors.BLUE,
        )
    )

    try:
        validate_byop_structure(model_path)

        typer.echo(
            typer.style(
                "\nBYOP validation PASSED!",
                fg=typer.colors.GREEN,
                bold=True,
            )
        )
        typer.echo("All validation checks completed successfully.")

    except BYOPValidationError as e:
        _exit_with_error(str(e), "BYOP validation FAILED")

    except FileNotFoundError as e:
        _exit_with_error(str(e), "File not found")

    except Exception as e:
        logger.exception("Unexpected error during BYOP validation")
        _exit_with_error(str(e), "Unexpected error during validation")
