"""This module features converter functions for numpy."""

import logging
from typing import Any, Dict, Iterable, List, Union

import numpy as np
import numpy.typing as npt
import pandas as pd

from pydata_util.numpy.data_inspectors import is_numpy_array_multi_dim

logger = logging.getLogger(__name__)


def convert_dataframe_to_dict_of_numpy_arrays(
    data: pd.DataFrame,
) -> Dict[str, npt.NDArray]:
    """Converts a Pandas DataFrame to a dict of numpy arrays.

    :param data: The data to convert.
    :raises ValueError: If the conversion fails.

    :return: The data converted to a dict of numpy arrays.
    """
    output = {}
    for col in data.columns:
        try:
            output[col] = np.array(data[col].tolist())
        except ValueError:
            message = (
                f"Could not convert column `{col}` to numpy array, due to ValueError. "
                "Converting to numpy array of lists instead."
            )
            logger.debug(message, exc_info=True)
            output[col] = np.array(data[col].tolist(), dtype=object)
    return output


def convert_dataframe_to_numpy(data: pd.DataFrame) -> npt.NDArray:
    """Converts a Pandas DataFrame to a numpy array.

    :param data: The data to convert.

    :return: The data converted to a numpy array.
    """
    return data.to_numpy()


def convert_dict_of_arrays_to_list_of_arrays(
    data: Dict[str, Iterable],
) -> List[Iterable]:
    """Converts a dict of arrays to a list of arrays preserving
    the key order.

    Example:

    {
        "output_1": np.array([1, 2, 3]),
        "output_2": np.array([4, 5, 6]),
    }

    converts to:
    [np.array([1, 2, 3]), np.array([4, 5, 6])]

    :param data: The data to convert.

    :return: The converted data.
    """
    return [data[key] for key in data]


def convert_list_of_arrays_to_dict_of_arrays(
    data: List[Iterable], expected_skeleton: str
) -> Dict[str, Iterable]:
    """Converts a list of arrays to a dict of arrays with sorted
    keys in ascending order.

    Example:
    {
        "output_1": np.array([1, 2, 3]),
        "output_2": np.array([4, 5, 6]),
    }

    :param data: The data to convert.
    :param expected_skeleton: The expected skeleton of the keys.

    :return: The converted data to a dict of iterables.
    """
    return {f"{expected_skeleton}_{i+1}": data for i, data in enumerate(data)}


def convert_list_of_dicts_to_dict_of_numpy_arrays(
    data: List[Dict[str, Any]], expected_keys: List[str]
) -> Dict[str, npt.NDArray]:
    """Converts a list of dicts to a dict of numpy arrays.

    :param data: The data to convert.
    :param expected_keys: The expected keys of the dicts.

    :return: The converted data to a dict of numpy arrays.
    """
    return {key: np.array([item[key] for item in data]) for key in expected_keys}


def convert_multi_dim_numpy_array_to_list(
    data: npt.NDArray,
) -> Union[List, npt.NDArray]:
    """Converts a multi-dimensional numpy array to a list.

    :param data: The data to convert.

    :return: The converted data.
    """
    if isinstance(data, np.ndarray) and is_numpy_array_multi_dim(data):
        return [convert_multi_dim_numpy_array_to_list(element) for element in data]
    return data.ravel() if isinstance(data, np.ndarray) else data
