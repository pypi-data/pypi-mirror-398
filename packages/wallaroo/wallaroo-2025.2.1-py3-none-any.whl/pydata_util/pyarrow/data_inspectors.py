"""This modules contains data inspection functions for pyarrow."""

from typing import List, Optional, Tuple, Union

import numpy as np
import pyarrow as pa

from pydata_util.types import IOArrowDType


def get_arrow_type_of_nested_arrow_list_type(
    arrow_type: Union[pa.ListType, pa.FixedSizeListType],
) -> int:  # pragma: no cover
    """Gets the PyArrow type of a nested PyArrow list.

    :param arrow_type: The nested list to get the type of.

    :return: The dtype id of the nested list.
    """
    if isinstance(arrow_type, (pa.ListType, pa.FixedSizeListType)):
        return get_arrow_type_of_nested_arrow_list_type(arrow_type.value_type)
    return arrow_type.id


def get_io_arrow_dtype_from_pa_dtype(
    pa_dtype: pa.DataType,
) -> IOArrowDType:  # pragma: no cover
    """Gets the `IOArrowDType` from the given `pa.DataType`.

    :param pa_dtype: The `pa.DataType` to get the `IOArrowDType` from.

    :return: The `IOArrowDType` of the column.
    """
    if isinstance(pa_dtype, pa.FixedShapeTensorType):
        return IOArrowDType.FIXED_SHAPE_TENSOR
    elif isinstance(pa_dtype, pa.FixedSizeListType):
        return IOArrowDType.FIXED_SIZE_LIST
    elif isinstance(pa_dtype, pa.ListType):
        return IOArrowDType.LIST
    else:
        return IOArrowDType.SCALAR


def get_non_null_indexes_from_list_array(
    array: Union[pa.ListArray, pa.FixedSizeListArray],
) -> List[int]:  # pragma: no cover
    """Gets the valid indexes from a list array.

    :param array: The list array to get the valid indexes from.

    :return: The valid indexes.
    """
    return [i for i, v in enumerate(array.is_valid()) if v.as_py()]


def get_numpy_type_of_list_array(
    pa_dtype: pa.DataType,
) -> Optional[np.dtype]:  # pragma: no cover
    """Get the data type of the list array.

    :param pa_dtype: The PyArrow data type of the list array.

    :return: The data type of the list array.
    """
    while pa_type_is_list(pa_dtype):
        pa_dtype = pa_dtype.value_type
    try:
        return pa_dtype.to_pandas_dtype()
    except NotImplementedError:
        return None


def get_shape_of_nested_arrow_list_type(
    arrow_type: pa.FixedSizeListType,
) -> Tuple[int, ...]:  # pragma: no cover
    """Gets the shape of a nested `pa.FixedSizeListType`.

    :param data: The nested list to get the shape of.

    :return: The shape of the nested list.
    """
    if isinstance(arrow_type, pa.FixedSizeListType):
        return (arrow_type.list_size,) + get_shape_of_nested_arrow_list_type(
            arrow_type.value_type
        )
    return ()


def get_shape_of_nested_pa_list_scalar(
    data: pa.ListScalar,
) -> Tuple[int, ...]:  # pragma: no cover
    """Gets the shape of a nested `pa.ListScalar`.

    :param data: The nested list to get the shape of.

    :return: The shape of the nested `pa.ListScalar`.
    """
    if isinstance(data, pa.ListScalar):
        if data.is_valid:
            return (len(data),) + get_shape_of_nested_pa_list_scalar(data[0])
        return (0,)
    return ()


def pa_type_is_list(data_type: pa.DataType) -> bool:  # pragma: no cover
    """Checks if the given PyArrow data type is a list type.

    :param data_type: The data type to check.

    :return: True if the given data type is a list type, False otherwise.
    """
    return isinstance(data_type, (pa.ListType, pa.FixedSizeListType))
