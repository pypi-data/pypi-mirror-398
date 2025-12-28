"""This module features PickleLoader, that implements the loader for Pickle files."""

import logging
import pickle
from pathlib import Path
from typing import Callable, Set

from pydata_util.file_loading.file_loader import FileLoader

logger = logging.getLogger(__name__)


class PickleLoader(FileLoader):
    """This class extends FileLoader and can load a Pickle file to a Callable
    from a given path.

    Attributes:
        supported_file_formats: The supported file formats for the loader.
    """

    @property
    def supported_file_formats(self) -> Set[str]:
        """Return the supported file formats for the loader."""
        return {"pkl", "pickle"}

    def _load_file(self, file_path: Path) -> Callable:
        """Load a pickle file given a path.

        :param file_path: Path to the pickle file.

        :return: Serialized pickle object.
        """
        logger.info(f"Loading Pickle file from '{file_path.as_posix()}'...")

        with open(file_path, "rb") as pickle_file:
            data = pickle.load(pickle_file)

        logger.info("Loading successful.")

        return data
