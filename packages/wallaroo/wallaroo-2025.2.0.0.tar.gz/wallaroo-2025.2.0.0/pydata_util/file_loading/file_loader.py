"""This module features the FileLoader interface, that can be extended
to implement a loader for a specific file format."""

import logging
from abc import abstractmethod
from pathlib import Path
from typing import Any, Set

from pydata_util.exceptions import (
    raise_file_format_error_if_file_format_incorrect,
    raise_path_not_exist_error_if_no_path,
)

logger = logging.getLogger(__name__)


class FileLoader:
    """This class implements the FileLoader interface, that can be extended
    to implement a loader for a specific file format.

    Attributes:
        - supported_file_formats: The supported file formats for the loader.
    """

    @property
    @abstractmethod
    def supported_file_formats(self) -> Set[str]:
        """Return the supported file formats for the loader."""

    def load(self, file_path: Path) -> Any:
        """Load a file given a path.

        :param file_path: Path to the file.

        :raises FileNotFoundError: If the file does not exist.
        :raises FileFormatError: If the file format is not supported.

        :return: The loaded file.
        """
        raise_path_not_exist_error_if_no_path(file_path)
        raise_file_format_error_if_file_format_incorrect(
            file_path, supported_file_formats=self.supported_file_formats
        )
        data = self._load_file(file_path)

        return data

    @abstractmethod
    def _load_file(self, file_path: Path) -> Any:
        """Load a file given a path.

        :param file_path: Path to the file.

        :return: The loaded file.
        """
