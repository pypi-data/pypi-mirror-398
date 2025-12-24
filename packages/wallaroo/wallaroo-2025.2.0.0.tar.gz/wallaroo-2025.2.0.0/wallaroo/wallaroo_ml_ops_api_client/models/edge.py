import datetime
from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.app_version import AppVersion
from ..types import UNSET, Unset

T = TypeVar("T", bound="Edge")


@_attrs_define
class Edge:
    """The Edge

    Attributes:
        cpus (float): Number of CPUs
        id (UUID): ID
        memory (str): Amount of memory (in k8s format)
        name (str): User-given name
        tags (list[str]): Edge tags
        created_at (Union[None, Unset, datetime.datetime]): Date created
        created_on_version (Union[Unset, AppVersion]):
        should_run_publish (Union[None, Unset, int]): The pipeline publish ID this edge is supposed to run
        spiffe_id (Union[None, Unset, str]): Spiffe ID
    """

    cpus: float
    id: UUID
    memory: str
    name: str
    tags: list[str]
    created_at: Union[None, Unset, datetime.datetime] = UNSET
    created_on_version: Union[Unset, AppVersion] = UNSET
    should_run_publish: Union[None, Unset, int] = UNSET
    spiffe_id: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cpus = self.cpus

        id = str(self.id)

        memory = self.memory

        name = self.name

        tags = self.tags

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        created_on_version: Union[Unset, str] = UNSET
        if not isinstance(self.created_on_version, Unset):
            created_on_version = self.created_on_version.value

        should_run_publish: Union[None, Unset, int]
        if isinstance(self.should_run_publish, Unset):
            should_run_publish = UNSET
        else:
            should_run_publish = self.should_run_publish

        spiffe_id: Union[None, Unset, str]
        if isinstance(self.spiffe_id, Unset):
            spiffe_id = UNSET
        else:
            spiffe_id = self.spiffe_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "cpus": cpus,
                "id": id,
                "memory": memory,
                "name": name,
                "tags": tags,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if created_on_version is not UNSET:
            field_dict["created_on_version"] = created_on_version
        if should_run_publish is not UNSET:
            field_dict["should_run_publish"] = should_run_publish
        if spiffe_id is not UNSET:
            field_dict["spiffe_id"] = spiffe_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cpus = d.pop("cpus")

        id = UUID(d.pop("id"))

        memory = d.pop("memory")

        name = d.pop("name")

        tags = cast(list[str], d.pop("tags"))

        def _parse_created_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        _created_on_version = d.pop("created_on_version", UNSET)
        created_on_version: Union[Unset, AppVersion]
        if isinstance(_created_on_version, Unset):
            created_on_version = UNSET
        else:
            created_on_version = AppVersion(_created_on_version)

        def _parse_should_run_publish(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        should_run_publish = _parse_should_run_publish(
            d.pop("should_run_publish", UNSET)
        )

        def _parse_spiffe_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        spiffe_id = _parse_spiffe_id(d.pop("spiffe_id", UNSET))

        edge = cls(
            cpus=cpus,
            id=id,
            memory=memory,
            name=name,
            tags=tags,
            created_at=created_at,
            created_on_version=created_on_version,
            should_run_publish=should_run_publish,
            spiffe_id=spiffe_id,
        )

        edge.additional_properties = d
        return edge

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
