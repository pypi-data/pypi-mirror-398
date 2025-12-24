"""This module contains helper functions for numpy arrays."""

from typing import Optional, Tuple

import numpy as np
import numpy.typing as npt


def create_numpy_array_of_nulls(
    shape: Tuple[int, ...], numpy_dtype: Optional[np.dtype] = None
) -> npt.NDArray:
    """Creates a numpy array with null values.

    :param shape: The shape of the numpy array.
    :param numpy_dtype: The numpy data type.

    :return: The numpy array with null values.
    """
    return (
        np.full(shape, np.nan).astype(numpy_dtype)
        if numpy_dtype
        else np.full(shape, np.nan)
    )


def convert_numpy_object_array_to_fixed_shape(data: npt.NDArray) -> npt.NDArray:
    """Converts a numpy object array to a fixed shape numpy array if possible.

    :param data: The numpy object array to convert.

    :return: The converted data to a fixed shape numpy array.
    """
    if isinstance(data, np.ndarray) and data.dtype == object:
        return np.array([convert_numpy_object_array_to_fixed_shape(i) for i in data])
    return data
