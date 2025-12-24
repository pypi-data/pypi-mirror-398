from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="FileInfo")


@_attrs_define
class FileInfo:
    """
    Attributes:
        file_name (str):
        sha (str):
        size (int):
        version (UUID):
    """

    file_name: str
    sha: str
    size: int
    version: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file_name = self.file_name

        sha = self.sha

        size = self.size

        version = str(self.version)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file_name": file_name,
                "sha": sha,
                "size": size,
                "version": version,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file_name = d.pop("file_name")

        sha = d.pop("sha")

        size = d.pop("size")

        version = UUID(d.pop("version"))

        file_info = cls(
            file_name=file_name,
            sha=sha,
            size=size,
            version=version,
        )

        file_info.additional_properties = d
        return file_info

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
