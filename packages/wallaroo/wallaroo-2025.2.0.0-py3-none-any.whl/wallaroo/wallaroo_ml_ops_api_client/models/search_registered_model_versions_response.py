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
    from ..models.registered_model_version import RegisteredModelVersion


T = TypeVar("T", bound="SearchRegisteredModelVersionsResponse")


@_attrs_define
class SearchRegisteredModelVersionsResponse:
    """The structure of the response from a 2.0 MLFlow API.

    Attributes:
        model_versions (list['RegisteredModelVersion']):
        next_page_token (Union[None, Unset, str]):
    """

    model_versions: list["RegisteredModelVersion"]
    next_page_token: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model_versions = []
        for model_versions_item_data in self.model_versions:
            model_versions_item = model_versions_item_data.to_dict()
            model_versions.append(model_versions_item)

        next_page_token: Union[None, Unset, str]
        if isinstance(self.next_page_token, Unset):
            next_page_token = UNSET
        else:
            next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model_versions": model_versions,
            }
        )
        if next_page_token is not UNSET:
            field_dict["next_page_token"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.registered_model_version import RegisteredModelVersion

        d = dict(src_dict)
        model_versions = []
        _model_versions = d.pop("model_versions")
        for model_versions_item_data in _model_versions:
            model_versions_item = RegisteredModelVersion.from_dict(
                model_versions_item_data
            )

            model_versions.append(model_versions_item)

        def _parse_next_page_token(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        next_page_token = _parse_next_page_token(d.pop("next_page_token", UNSET))

        search_registered_model_versions_response = cls(
            model_versions=model_versions,
            next_page_token=next_page_token,
        )

        search_registered_model_versions_response.additional_properties = d
        return search_registered_model_versions_response

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
