from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="DbfsListResponseFile")


@_attrs_define
class DbfsListResponseFile:
    """A dbfs file entry

    Attributes:
        file_size (int):
        is_dir (bool):
        modification_time (int):
        path (str):
    """

    file_size: int
    is_dir: bool
    modification_time: int
    path: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file_size = self.file_size

        is_dir = self.is_dir

        modification_time = self.modification_time

        path = self.path

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file_size": file_size,
                "is_dir": is_dir,
                "modification_time": modification_time,
                "path": path,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file_size = d.pop("file_size")

        is_dir = d.pop("is_dir")

        modification_time = d.pop("modification_time")

        path = d.pop("path")

        dbfs_list_response_file = cls(
            file_size=file_size,
            is_dir=is_dir,
            modification_time=modification_time,
            path=path,
        )

        dbfs_list_response_file.additional_properties = d
        return dbfs_list_response_file

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
