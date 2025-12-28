"""This module features converter functions for pyarrow."""

import functools
import logging
import operator
from typing import List, Optional, Union

import numpy as np
import numpy.typing as npt
import pyarrow as pa

from pydata_util.numpy.converters import convert_multi_dim_numpy_array_to_list
from pydata_util.numpy.helpers import (
    convert_numpy_object_array_to_fixed_shape,
    create_numpy_array_of_nulls,
)
from pydata_util.pyarrow.data_inspectors import (
    get_non_null_indexes_from_list_array,
    get_numpy_type_of_list_array,
    get_shape_of_nested_pa_list_scalar,
    pa_type_is_list,
)

logger = logging.getLogger(__name__)


def convert_fixed_shape_tensor_array_to_numpy_array(
    array: pa.FixedShapeTensorArray,
) -> npt.NDArray:
    """Converts a `pa.FixedShapeTensorArray` to a numpy array.

    :param array: The `pa.FixedShapeTensorArray` object to convert.
        The first dimension is the batch size.

    :return: The converted data to a fixed shape numpy array.
    """
    return array.to_numpy_ndarray()


def convert_nested_list_array_to_fixed_shape_numpy_array(
    array: Union[pa.ListArray, pa.FixedSizeListArray],
    is_nullable: Optional[bool] = True,
) -> npt.NDArray:  # pragma: no cover
    """Converts a `pa.ListArray` or `pa.FixedSizeListArray` to a fixed shape
    numpy array.

    :param array: The `pa.ListArray` or `pa.FixedSizeListArray` object to convert.
        The first dimension is the batch size.
    :param is_nullable: Whether the array is nullable.

    :return: The converted data to a fixed shape numpy array.
    """
    if is_nullable:
        return convert_nullable_list_array_to_fixed_shape_numpy_array(array)
    return convert_non_nullable_list_array_to_fixed_shape_numpy_array(array)


def convert_non_nullable_list_array_to_fixed_shape_numpy_array(
    array: Union[pa.ListArray, pa.FixedSizeListArray],
) -> npt.NDArray:  # pragma: no cover
    """Converts a `pa.ListArray` or `pa.FixedSizeListArray` to a fixed shape
    numpy array.

    :param array: The `pa.ListArray` or `pa.FixedSizeListArray` object to convert.
        The first dimension is the batch size.

    :return: The converted data to a fixed shape numpy array.
    """
    batch_len = len(array)
    shape = get_shape_of_nested_pa_list_scalar(array[0])
    num_nested_items = functools.reduce(operator.mul, shape)

    return np.array(
        [
            flat_values(array, i, num_nested_items)
            .to_numpy(zero_copy_only=False)
            .reshape(*shape)
            for i in range(batch_len)
        ]
    )


def convert_nullable_list_array_to_fixed_shape_numpy_array(
    array: Union[pa.ListArray, pa.FixedSizeListArray],
) -> npt.NDArray:  # pragma: no cover
    """Converts a `pa.ListArray` or `pa.FixedSizeListArray` to a fixed shape
    numpy array. Since the array is nullable, it also checks for `Null` values
    and fills them with `np.nan`.

    :param array: The `pa.ListArray` or `pa.FixedSizeListArray` object to convert.
        The first dimension is the batch size.

    :return: The converted data to a fixed shape numpy array.
    """
    batch_len = len(array)
    numpy_dtype = get_numpy_type_of_list_array(array.type)

    non_null_indexes = get_non_null_indexes_from_list_array(array)
    if not non_null_indexes:
        # return a batch of np.nan if the batch only contains `Null` values
        return create_numpy_array_of_nulls(shape=(batch_len,), numpy_dtype=numpy_dtype)
    null_indexes = [i for i in range(batch_len) if i not in non_null_indexes]

    shape = get_shape_of_nested_pa_list_scalar(array[non_null_indexes[0]])
    num_nested_items = functools.reduce(operator.mul, shape)

    return np.array(
        [
            (
                flat_values(array, i, num_nested_items, null_indexes)
                .to_numpy(zero_copy_only=False)
                .reshape(*shape)
                if i in non_null_indexes
                else create_numpy_array_of_nulls(shape=shape, numpy_dtype=numpy_dtype)
            )
            for i in range(batch_len)
        ]
    )


def convert_nested_list_array_to_nested_numpy_array(
    array: Union[pa.ListArray, pa.FixedSizeListArray],
) -> npt.NDArray:
    """Converts a `pa.ListArray` or `pa.FixedSizeListArray`
    to a numpy array. The function will attempt to convert
    the array to a fixed shape numpy array first, and if that fails,
    it will convert the array to a numpy array of type object.

    :param array: The `pa.ListArray` or `pa.FixedSizeListArray` to convert.
        The first dimension is the batch size.
    :raises ValueError: If the array is not convertible to fixed shape.

    :return: The converted data to a numpy array that is either of type `np.object`
        or a fixed shape one.
    """
    data = array.to_numpy(zero_copy_only=False)
    try:
        return convert_numpy_object_array_to_fixed_shape(data)
    except ValueError:
        return data


def convert_nested_list_array_to_numpy_array(
    array: Union[pa.ListArray, pa.FixedSizeListArray],
    is_nullable: Optional[bool] = True,
) -> npt.NDArray:  # pragma: no cover
    """Converts a `pa.ListArray` or `pa.FixedSizeListArray`
    to a nested numpy array taking care of Null values if requested
    (i.e. via the `is_nullable` flag). Since neither of the two guarantees
    a fixed shape, we always try to convert to a fixed shape numpy array first.
    If that fails, we convert to a nested numpy array of type object.

    :param array: The `pa.ListArray` or `pa.FixedSizeListArray` object to convert.
        The first dimension is the batch size.
    :param is_nullable: Whether the array is nullable.
    :raises ValueError: If the array is not convertible to fixed shape.

    :return: The converted data to a numpy array of type `np.object`.
    """
    try:
        return convert_nested_list_array_to_fixed_shape_numpy_array(array, is_nullable)
    except (ValueError, IndexError):
        # The incoming array is not of fixed shape, so we need to at least
        # return a numpy array of type object.
        return convert_nested_list_array_to_nested_numpy_array(array)


def convert_numpy_array_to_fixed_shape_tensor_array(
    data: npt.NDArray,
) -> pa.FixedShapeTensorArray:
    """Converts a multi dim numpy array to a `pa.FixedShapeTensorArray`.

    :param data: The data to convert. The first dimension is the batch size.

    :return: The converted data to a `pa.FixedShapeTensorArray`.
    """
    return pa.FixedShapeTensorArray.from_numpy_ndarray(data)


def convert_numpy_array_to_nested_list_array(
    data: npt.NDArray, pa_dtype: pa.DataType
) -> pa.ListArray:
    """Converts a numpy array to a nested list array.

    :param data: The data to convert.
    :param pa_dtype: The PyArrow data type of the data.

    :return: The converted data to a nested list array,
        along with the PyArrow data type.
    """
    return pa.array(
        convert_multi_dim_numpy_array_to_list(data),
        type=pa_dtype,
    )


def convert_numpy_array_to_scalar_array(
    data: npt.NDArray,
) -> pa.Array:
    """Converts a scalar numpy array to a `pa.Array`.

    :param data: The data to convert.

    :return: The converted data to a `pa.Array`.
    """
    return pa.array(data)


def convert_scalar_array_to_numpy_array(
    array: Union[pa.Array, pa.NumericArray],
) -> npt.NDArray:
    """Converts a scalar array to a numpy array.

    :param array: The scalar array to convert.
        The first dimension is the batch size.

    :return: The converted data to a numpy array.
    """
    return array.to_numpy(zero_copy_only=False)


def flat_values(
    array: Union[pa.ListArray, pa.FixedSizeListArray],
    offset: int,
    num_nested_items: int,
    null_indexes: Optional[List[int]] = None,  # noqa: F821
) -> pa.Array:  # pragma: no cover
    """
    Recursively un-nest a `pa.ListArray` or `pa.FixedSizeListArray`
    until a non-list type is found.

    :param array: The `pa.ListArray` or `pa.FixedSizeListArray` object to flatten.
    :param offset: The offset to slice the array.
    :param num_nested_items: The number of total items to slice from the array.
        The slice operation is zero-copy.
    :param null_indexes: The list of null indexes to skip.

    :return: The inner non-nested values array.
    """
    while pa_type_is_list(array.type):
        array = array.values

    if null_indexes:
        offset -= len([i for i in null_indexes if i < offset])

    return array.slice(offset * num_nested_items, num_nested_items)
