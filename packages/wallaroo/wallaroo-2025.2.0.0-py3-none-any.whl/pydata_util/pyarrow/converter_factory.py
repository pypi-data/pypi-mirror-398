"""This module features the `ArrowToNDArrayFactory` & `NDArrayToArrowFactory`
for creating concrete `ArrowToNDArrayConverter` & `ArrowToNDArrayConverter`
instances respectively."""

from typing import Dict

from pydata_util.creation import AbstractFactory
from pydata_util.pyarrow.converters import (
    convert_fixed_shape_tensor_array_to_numpy_array,
    convert_nested_list_array_to_nested_numpy_array,
    convert_numpy_array_to_fixed_shape_tensor_array,
    convert_numpy_array_to_nested_list_array,
    convert_numpy_array_to_scalar_array,
    convert_scalar_array_to_numpy_array,
)
from pydata_util.types import (
    ArrowToNDArrayConverter,
    IOArrowDType,
    NDArrayToArrowConverter,
)

ARROW_TO_ND_ARRAY_CONVERTERS: Dict[IOArrowDType, ArrowToNDArrayConverter] = {
    IOArrowDType.FIXED_SIZE_LIST: convert_nested_list_array_to_nested_numpy_array,
    IOArrowDType.FIXED_SHAPE_TENSOR: convert_fixed_shape_tensor_array_to_numpy_array,
    IOArrowDType.LIST: convert_nested_list_array_to_nested_numpy_array,
    IOArrowDType.SCALAR: convert_scalar_array_to_numpy_array,
}


ND_ARRAY_TO_ARROW_CONVERTERS: Dict[IOArrowDType, NDArrayToArrowConverter] = {
    IOArrowDType.FIXED_SIZE_LIST: convert_numpy_array_to_nested_list_array,  # type: ignore[dict-item]
    IOArrowDType.FIXED_SHAPE_TENSOR: convert_numpy_array_to_fixed_shape_tensor_array,
    IOArrowDType.LIST: convert_numpy_array_to_nested_list_array,  # type: ignore[dict-item]
    IOArrowDType.SCALAR: convert_numpy_array_to_scalar_array,
}


class ArrowToNDArrayFactory(AbstractFactory):
    """This class implements the AbstractFactory interface
    for creating concrete `ArrowToNDArrayConverter` functions."""

    @property
    def subclass_creators(self) -> dict:
        """Returns a dictionary of supported `ArrowToNDArrayConverter`
        functions.

        :return: A dictionary of subclass creators.
        """
        return ARROW_TO_ND_ARRAY_CONVERTERS


class NDArrayToArrowFactory(AbstractFactory):
    """This class implements the AbstractFactory interface
    for creating concrete `NDArrayToArrowConverter` functions."""

    @property
    def subclass_creators(self) -> dict:
        """Returns a dictionary of supported `NDArrayToArrowConverter`
        functions.

        :return: A dictionary of subclass creators.
        """
        return ND_ARRAY_TO_ARROW_CONVERTERS
