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

T = TypeVar("T", bound="ModelsGetResponse200ModelsItem")


@_attrs_define
class ModelsGetResponse200ModelsItem:
    """Individual model details.

    Attributes:
        sha (str):  Model's content hash.
        models_pk_id (int):  Internal model identifer.
        model_version (str):  Model version.
        owner_id (str):  Model owner identifier.
        model_id (str):  Model identifier.
        id (int):  Internal identifier.
        file_name (Union[None, Unset, str]):  Model filename.
        image_path (Union[None, Unset, str]):  Model image path.
    """

    sha: str
    models_pk_id: int
    model_version: str
    owner_id: str
    model_id: str
    id: int
    file_name: Union[None, Unset, str] = UNSET
    image_path: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        sha = self.sha

        models_pk_id = self.models_pk_id

        model_version = self.model_version

        owner_id = self.owner_id

        model_id = self.model_id

        id = self.id

        file_name: Union[None, Unset, str]
        if isinstance(self.file_name, Unset):
            file_name = UNSET
        else:
            file_name = self.file_name

        image_path: Union[None, Unset, str]
        if isinstance(self.image_path, Unset):
            image_path = UNSET
        else:
            image_path = self.image_path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sha": sha,
                "models_pk_id": models_pk_id,
                "model_version": model_version,
                "owner_id": owner_id,
                "model_id": model_id,
                "id": id,
            }
        )
        if file_name is not UNSET:
            field_dict["file_name"] = file_name
        if image_path is not UNSET:
            field_dict["image_path"] = image_path

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sha = d.pop("sha")

        models_pk_id = d.pop("models_pk_id")

        model_version = d.pop("model_version")

        owner_id = d.pop("owner_id")

        model_id = d.pop("model_id")

        id = d.pop("id")

        def _parse_file_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        file_name = _parse_file_name(d.pop("file_name", UNSET))

        def _parse_image_path(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        image_path = _parse_image_path(d.pop("image_path", UNSET))

        models_get_response_200_models_item = cls(
            sha=sha,
            models_pk_id=models_pk_id,
            model_version=model_version,
            owner_id=owner_id,
            model_id=model_id,
            id=id,
            file_name=file_name,
            image_path=image_path,
        )

        models_get_response_200_models_item.additional_properties = d
        return models_get_response_200_models_item

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
