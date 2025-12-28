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
    from ..models.registered_model import RegisteredModel


T = TypeVar("T", bound="ListRegistryModelsResponse200")


@_attrs_define
class ListRegistryModelsResponse200:
    """The structure of the response from a 2.0 MLFlow API.

    Attributes:
        registered_models (list['RegisteredModel']):
        next_page_token (Union[None, Unset, str]):
    """

    registered_models: list["RegisteredModel"]
    next_page_token: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        registered_models = []
        for registered_models_item_data in self.registered_models:
            registered_models_item = registered_models_item_data.to_dict()
            registered_models.append(registered_models_item)

        next_page_token: Union[None, Unset, str]
        if isinstance(self.next_page_token, Unset):
            next_page_token = UNSET
        else:
            next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "registered_models": registered_models,
            }
        )
        if next_page_token is not UNSET:
            field_dict["next_page_token"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.registered_model import RegisteredModel

        d = dict(src_dict)
        registered_models = []
        _registered_models = d.pop("registered_models")
        for registered_models_item_data in _registered_models:
            registered_models_item = RegisteredModel.from_dict(
                registered_models_item_data
            )

            registered_models.append(registered_models_item)

        def _parse_next_page_token(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        next_page_token = _parse_next_page_token(d.pop("next_page_token", UNSET))

        list_registry_models_response_200 = cls(
            registered_models=registered_models,
            next_page_token=next_page_token,
        )

        list_registry_models_response_200.additional_properties = d
        return list_registry_models_response_200

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
