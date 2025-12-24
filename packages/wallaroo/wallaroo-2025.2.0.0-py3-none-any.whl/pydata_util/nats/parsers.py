"""This module features parsers for the NATSMessage dataclass."""

import json
import logging
from pathlib import Path

from pydata_util.file_loading import JSONLoader
from pydata_util.nats import NATSMessage, NATSMessageFactory
from pydata_util.types import SupportedNATSMessages

logger = logging.getLogger(__name__)


def parse_nats_message_from_model_json(
    file_path: Path, message_type: SupportedNATSMessages
) -> NATSMessage:
    """Parse the given `model.json` file and return a
    NATSMessage dataclass.

    :param file_path: The path of the `model.json` file to parse.
    :param message_type: The type of NATSMessage to create.
    :param supported_frameworks: The supported frameworks for the NATSMessage.

    :return: The parsed NATSMessage dataclass.
    """

    config = JSONLoader().load(file_path=file_path)
    return NATSMessageFactory().create(message_type, **config)


def save_nats_message_to_json(nats_message: NATSMessage, save_path: Path) -> None:
    """Save a NATSMessage to a JSON file.

    :param nats_message: The NATSMessage object to save.
    :param save_path: The path to the JSON file.
    """
    nats_message_json = nats_message.model_dump(mode="json")

    logger.info(f"Saving NATSMessage to '{save_path.as_posix()}'...")

    with open(save_path, "w", encoding="utf-8") as fp:
        json.dump(nats_message_json, fp)
