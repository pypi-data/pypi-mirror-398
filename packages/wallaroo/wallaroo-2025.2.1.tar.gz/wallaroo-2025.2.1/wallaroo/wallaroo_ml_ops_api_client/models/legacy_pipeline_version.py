from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
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

from ..models.app_version import AppVersion
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.legacy_pipeline_version_steps import LegacyPipelineVersionSteps


T = TypeVar("T", bound="LegacyPipelineVersion")


@_attrs_define
class LegacyPipelineVersion:
    """
    Attributes:
        id (str):
        workspace_id (int):
        created_at (Union[None, Unset, str]):
        created_by (Union[None, Unset, str]):
        created_on_version (Union[Unset, AppVersion]):
        steps (Union[Unset, LegacyPipelineVersionSteps]):
        version (Union[Unset, UUID]):
    """

    id: str
    workspace_id: int
    created_at: Union[None, Unset, str] = UNSET
    created_by: Union[None, Unset, str] = UNSET
    created_on_version: Union[Unset, AppVersion] = UNSET
    steps: Union[Unset, "LegacyPipelineVersionSteps"] = UNSET
    version: Union[Unset, UUID] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        workspace_id = self.workspace_id

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        created_by: Union[None, Unset, str]
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        else:
            created_by = self.created_by

        created_on_version: Union[Unset, str] = UNSET
        if not isinstance(self.created_on_version, Unset):
            created_on_version = self.created_on_version.value

        steps: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.steps, Unset):
            steps = self.steps.to_dict()

        version: Union[Unset, str] = UNSET
        if not isinstance(self.version, Unset):
            version = str(self.version)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "workspace_id": workspace_id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if created_on_version is not UNSET:
            field_dict["created_on_version"] = created_on_version
        if steps is not UNSET:
            field_dict["steps"] = steps
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.legacy_pipeline_version_steps import LegacyPipelineVersionSteps

        d = dict(src_dict)
        id = d.pop("id")

        workspace_id = d.pop("workspace_id")

        def _parse_created_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_created_by(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_by = _parse_created_by(d.pop("created_by", UNSET))

        _created_on_version = d.pop("created_on_version", UNSET)
        created_on_version: Union[Unset, AppVersion]
        if isinstance(_created_on_version, Unset):
            created_on_version = UNSET
        else:
            created_on_version = AppVersion(_created_on_version)

        _steps = d.pop("steps", UNSET)
        steps: Union[Unset, LegacyPipelineVersionSteps]
        if isinstance(_steps, Unset):
            steps = UNSET
        else:
            steps = LegacyPipelineVersionSteps.from_dict(_steps)

        _version = d.pop("version", UNSET)
        version: Union[Unset, UUID]
        if isinstance(_version, Unset):
            version = UNSET
        else:
            version = UUID(_version)

        legacy_pipeline_version = cls(
            id=id,
            workspace_id=workspace_id,
            created_at=created_at,
            created_by=created_by,
            created_on_version=created_on_version,
            steps=steps,
            version=version,
        )

        legacy_pipeline_version.additional_properties = d
        return legacy_pipeline_version

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
