from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.v1_model_get_config_response_200_model_config_type_0_tensor_fields_type_0 import (
        V1ModelGetConfigResponse200ModelConfigType0TensorFieldsType0,
    )


T = TypeVar("T", bound="V1ModelGetConfigResponse200ModelConfigType0")


@_attrs_define
class V1ModelGetConfigResponse200ModelConfigType0:
    """An optional Model Configuration

    Attributes:
        id (int):  The primary id of the model configuration.
        runtime (str):  The model configuration runtime.
        tensor_fields (Union['V1ModelGetConfigResponse200ModelConfigType0TensorFieldsType0', None, Unset]):  Optional
            Tensor Fields for the model.
        filter_threshold (Union[None, Unset, float]):  An optional filter threshold
    """

    id: int
    runtime: str
    tensor_fields: Union[
        "V1ModelGetConfigResponse200ModelConfigType0TensorFieldsType0", None, Unset
    ] = UNSET
    filter_threshold: Union[None, Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.v1_model_get_config_response_200_model_config_type_0_tensor_fields_type_0 import (
            V1ModelGetConfigResponse200ModelConfigType0TensorFieldsType0,
        )

        id = self.id

        runtime = self.runtime

        tensor_fields: Union[None, Unset, dict[str, Any]]
        if isinstance(self.tensor_fields, Unset):
            tensor_fields = UNSET
        elif isinstance(
            self.tensor_fields,
            V1ModelGetConfigResponse200ModelConfigType0TensorFieldsType0,
        ):
            tensor_fields = self.tensor_fields.to_dict()
        else:
            tensor_fields = self.tensor_fields

        filter_threshold: Union[None, Unset, float]
        if isinstance(self.filter_threshold, Unset):
            filter_threshold = UNSET
        else:
            filter_threshold = self.filter_threshold

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "runtime": runtime,
            }
        )
        if tensor_fields is not UNSET:
            field_dict["tensor_fields"] = tensor_fields
        if filter_threshold is not UNSET:
            field_dict["filter_threshold"] = filter_threshold

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.v1_model_get_config_response_200_model_config_type_0_tensor_fields_type_0 import (
            V1ModelGetConfigResponse200ModelConfigType0TensorFieldsType0,
        )

        d = dict(src_dict)
        id = d.pop("id")

        runtime = d.pop("runtime")

        def _parse_tensor_fields(
            data: object,
        ) -> Union[
            "V1ModelGetConfigResponse200ModelConfigType0TensorFieldsType0", None, Unset
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                tensor_fields_type_0 = V1ModelGetConfigResponse200ModelConfigType0TensorFieldsType0.from_dict(
                    data
                )

                return tensor_fields_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "V1ModelGetConfigResponse200ModelConfigType0TensorFieldsType0",
                    None,
                    Unset,
                ],
                data,
            )

        tensor_fields = _parse_tensor_fields(d.pop("tensor_fields", UNSET))

        def _parse_filter_threshold(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        filter_threshold = _parse_filter_threshold(d.pop("filter_threshold", UNSET))

        v1_model_get_config_response_200_model_config_type_0 = cls(
            id=id,
            runtime=runtime,
            tensor_fields=tensor_fields,
            filter_threshold=filter_threshold,
        )

        v1_model_get_config_response_200_model_config_type_0.additional_properties = d
        return v1_model_get_config_response_200_model_config_type_0

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
