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


T = TypeVar("T", bound="RegisteredModel")


@_attrs_define
class RegisteredModel:
    """A [RegisteredModel] is an MLFlow concept for a model that has been logged in MLFlow.
    For more information, see <https://mlflow.org/docs/latest/model-registry.html#concepts>

        Attributes:
            creation_timestamp (int): Timestamp in milliseconds from epoch
            last_updated_timestamp (int): Timestamp in milliseconds from epoch
            name (str):
            user_id (str):
            latest_versions (Union[None, Unset, list['RegisteredModelVersion']]):
    """

    creation_timestamp: int
    last_updated_timestamp: int
    name: str
    user_id: str
    latest_versions: Union[None, Unset, list["RegisteredModelVersion"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        creation_timestamp = self.creation_timestamp

        last_updated_timestamp = self.last_updated_timestamp

        name = self.name

        user_id = self.user_id

        latest_versions: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.latest_versions, Unset):
            latest_versions = UNSET
        elif isinstance(self.latest_versions, list):
            latest_versions = []
            for latest_versions_type_0_item_data in self.latest_versions:
                latest_versions_type_0_item = latest_versions_type_0_item_data.to_dict()
                latest_versions.append(latest_versions_type_0_item)

        else:
            latest_versions = self.latest_versions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "creation_timestamp": creation_timestamp,
                "last_updated_timestamp": last_updated_timestamp,
                "name": name,
                "user_id": user_id,
            }
        )
        if latest_versions is not UNSET:
            field_dict["latest_versions"] = latest_versions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.registered_model_version import RegisteredModelVersion

        d = dict(src_dict)
        creation_timestamp = d.pop("creation_timestamp")

        last_updated_timestamp = d.pop("last_updated_timestamp")

        name = d.pop("name")

        user_id = d.pop("user_id")

        def _parse_latest_versions(
            data: object,
        ) -> Union[None, Unset, list["RegisteredModelVersion"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                latest_versions_type_0 = []
                _latest_versions_type_0 = data
                for latest_versions_type_0_item_data in _latest_versions_type_0:
                    latest_versions_type_0_item = RegisteredModelVersion.from_dict(
                        latest_versions_type_0_item_data
                    )

                    latest_versions_type_0.append(latest_versions_type_0_item)

                return latest_versions_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["RegisteredModelVersion"]], data)

        latest_versions = _parse_latest_versions(d.pop("latest_versions", UNSET))

        registered_model = cls(
            creation_timestamp=creation_timestamp,
            last_updated_timestamp=last_updated_timestamp,
            name=name,
            user_id=user_id,
            latest_versions=latest_versions,
        )

        registered_model.additional_properties = d
        return registered_model

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
