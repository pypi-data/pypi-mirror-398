from collections.abc import Mapping
from typing import (
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

T = TypeVar("T", bound="ModelsListVersionsBody")


@_attrs_define
class ModelsListVersionsBody:
    """Request for getting model versions

    Attributes:
        model_id (Union[None, Unset, str]):  Descriptive identifier for the model
        models_pk_id (Union[None, Unset, int]):  Internal numeric identifier for the model
    """

    model_id: Union[None, Unset, str] = UNSET
    models_pk_id: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model_id: Union[None, Unset, str]
        if isinstance(self.model_id, Unset):
            model_id = UNSET
        else:
            model_id = self.model_id

        models_pk_id: Union[None, Unset, int]
        if isinstance(self.models_pk_id, Unset):
            models_pk_id = UNSET
        else:
            models_pk_id = self.models_pk_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if model_id is not UNSET:
            field_dict["model_id"] = model_id
        if models_pk_id is not UNSET:
            field_dict["models_pk_id"] = models_pk_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_model_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        model_id = _parse_model_id(d.pop("model_id", UNSET))

        def _parse_models_pk_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        models_pk_id = _parse_models_pk_id(d.pop("models_pk_id", UNSET))

        models_list_versions_body = cls(
            model_id=model_id,
            models_pk_id=models_pk_id,
        )

        models_list_versions_body.additional_properties = d
        return models_list_versions_body

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
