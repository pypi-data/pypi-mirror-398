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

T = TypeVar("T", bound="RegisteredModelVersion")


@_attrs_define
class RegisteredModelVersion:
    """An MLFlow version of a [RegisteredModel]. Versions start at 1.

    Attributes:
        creation_timestamp (int): Timestamp in milliseconds from epoch
        current_stage (str):
        last_updated_timestamp (int): Timestamp in milliseconds from epoch
        name (str):
        run_id (str):
        source (str):
        status (str):
        version (str):
        description (Union[None, Unset, str]):
        run_link (Union[None, Unset, str]):
        user_id (Union[None, Unset, str]):
    """

    creation_timestamp: int
    current_stage: str
    last_updated_timestamp: int
    name: str
    run_id: str
    source: str
    status: str
    version: str
    description: Union[None, Unset, str] = UNSET
    run_link: Union[None, Unset, str] = UNSET
    user_id: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        creation_timestamp = self.creation_timestamp

        current_stage = self.current_stage

        last_updated_timestamp = self.last_updated_timestamp

        name = self.name

        run_id = self.run_id

        source = self.source

        status = self.status

        version = self.version

        description: Union[None, Unset, str]
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        run_link: Union[None, Unset, str]
        if isinstance(self.run_link, Unset):
            run_link = UNSET
        else:
            run_link = self.run_link

        user_id: Union[None, Unset, str]
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "creation_timestamp": creation_timestamp,
                "current_stage": current_stage,
                "last_updated_timestamp": last_updated_timestamp,
                "name": name,
                "run_id": run_id,
                "source": source,
                "status": status,
                "version": version,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if run_link is not UNSET:
            field_dict["run_link"] = run_link
        if user_id is not UNSET:
            field_dict["user_id"] = user_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        creation_timestamp = d.pop("creation_timestamp")

        current_stage = d.pop("current_stage")

        last_updated_timestamp = d.pop("last_updated_timestamp")

        name = d.pop("name")

        run_id = d.pop("run_id")

        source = d.pop("source")

        status = d.pop("status")

        version = d.pop("version")

        def _parse_description(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_run_link(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        run_link = _parse_run_link(d.pop("run_link", UNSET))

        def _parse_user_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        registered_model_version = cls(
            creation_timestamp=creation_timestamp,
            current_stage=current_stage,
            last_updated_timestamp=last_updated_timestamp,
            name=name,
            run_id=run_id,
            source=source,
            status=status,
            version=version,
            description=description,
            run_link=run_link,
            user_id=user_id,
        )

        registered_model_version.additional_properties = d
        return registered_model_version

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
