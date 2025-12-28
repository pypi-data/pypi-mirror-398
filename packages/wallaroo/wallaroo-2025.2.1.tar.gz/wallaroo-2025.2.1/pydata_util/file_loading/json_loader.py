"""This module implements the JSONLoader class for loading JSON configuration files."""

import json
import logging
from pathlib import Path
from typing import Dict, Set

from pydata_util.file_loading.file_loader import FileLoader

logger = logging.getLogger(__name__)


class JSONLoader(FileLoader):
    """This class extends FileLoader and can load a JSON file to a
    dictionary from a given path.

    Attributes:
        - encoding: Encoding of the JSON file.
        - supported_file_formats: The supported file formats for the loader.
    """

    def __init__(self, encoding="utf-8") -> None:
        self.encoding = encoding

    @property
    def supported_file_formats(self) -> Set[str]:
        """Return the supported file formats for the loader."""
        return {"json"}

    def _load_file(self, file_path: Path) -> Dict:
        """Load a pickle file given a path.

        :param file_path: Path to the pickle file.

        :return: Serialized pickle object.
        """
        logger.info(f"Loading JSON file from '{file_path.as_posix()}'...")

        with open(file_path, "r", encoding=self.encoding) as config_file:
            config = json.load(config_file)

        logger.info("Loading successful.")

        return config
