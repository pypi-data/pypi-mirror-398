"""This modules features data inspection functions for numpy."""

import numpy as np
import numpy.typing as npt


def is_numpy_array_multi_dim(data: npt.NDArray) -> bool:
    """Checks if the given numpy array is multi-dimensional.

    :param data: The numpy array to check.

    :return: True if the given numpy array is multi-dimensional, False otherwise.
    """
    if data.dtype == np.dtype("O"):
        return any(isinstance(item, (np.ndarray, list, dict)) for item in data)
    return data.ndim > 1
