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
    from ..models.features_list_response_200_features import (
        FeaturesListResponse200Features,
    )


T = TypeVar("T", bound="FeaturesListResponse200")


@_attrs_define
class FeaturesListResponse200:
    """
    Attributes:
        features (FeaturesListResponse200Features):
        name (str):
        is_auth_enabled (bool):
    """

    features: "FeaturesListResponse200Features"
    name: str
    is_auth_enabled: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        features = self.features.to_dict()

        name = self.name

        is_auth_enabled = self.is_auth_enabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "features": features,
                "name": name,
                "is_auth_enabled": is_auth_enabled,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.features_list_response_200_features import (
            FeaturesListResponse200Features,
        )

        d = dict(src_dict)
        features = FeaturesListResponse200Features.from_dict(d.pop("features"))

        name = d.pop("name")

        is_auth_enabled = d.pop("is_auth_enabled")

        features_list_response_200 = cls(
            features=features,
            name=name,
            is_auth_enabled=is_auth_enabled,
        )

        features_list_response_200.additional_properties = d
        return features_list_response_200

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
