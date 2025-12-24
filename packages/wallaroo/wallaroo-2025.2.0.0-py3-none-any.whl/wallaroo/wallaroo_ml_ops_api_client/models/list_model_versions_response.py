from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.configured_model_version import ConfiguredModelVersion


T = TypeVar("T", bound="ListModelVersionsResponse")


@_attrs_define
class ListModelVersionsResponse:
    """
    Attributes:
        model_versions (list['ConfiguredModelVersion']):
    """

    model_versions: list["ConfiguredModelVersion"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model_versions = []
        for model_versions_item_data in self.model_versions:
            model_versions_item = model_versions_item_data.to_dict()
            model_versions.append(model_versions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model_versions": model_versions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.configured_model_version import ConfiguredModelVersion

        d = dict(src_dict)
        model_versions = []
        _model_versions = d.pop("model_versions")
        for model_versions_item_data in _model_versions:
            model_versions_item = ConfiguredModelVersion.from_dict(
                model_versions_item_data
            )

            model_versions.append(model_versions_item)

        list_model_versions_response = cls(
            model_versions=model_versions,
        )

        list_model_versions_response.additional_properties = d
        return list_model_versions_response

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
