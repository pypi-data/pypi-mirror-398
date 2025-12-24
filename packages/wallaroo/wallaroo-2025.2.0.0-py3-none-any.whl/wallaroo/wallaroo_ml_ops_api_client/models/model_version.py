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

from ..models.app_version import AppVersion
from ..models.model_status import ModelStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.conversion import Conversion
    from ..models.file_info import FileInfo


T = TypeVar("T", bound="ModelVersion")


@_attrs_define
class ModelVersion:
    """
    Attributes:
        file_info (FileInfo):
        name (str):
        status (ModelStatus):
        visibility (str):
        workspace_id (int):
        conversion (Union['Conversion', None, Unset]):
        created_at (Union[None, Unset, str]):
        created_by (Union[None, Unset, str]):
        created_on_version (Union[Unset, AppVersion]):
        deployed (Union[Unset, bool]): True if any Deployments have an associated DeploymentModelConfig that associates
            with this model.
        id (Union[Unset, int]):
        image_path (Union[None, Unset, str]):
        task_id (Union[None, Unset, str]):
    """

    file_info: "FileInfo"
    name: str
    status: ModelStatus
    visibility: str
    workspace_id: int
    conversion: Union["Conversion", None, Unset] = UNSET
    created_at: Union[None, Unset, str] = UNSET
    created_by: Union[None, Unset, str] = UNSET
    created_on_version: Union[Unset, AppVersion] = UNSET
    deployed: Union[Unset, bool] = UNSET
    id: Union[Unset, int] = UNSET
    image_path: Union[None, Unset, str] = UNSET
    task_id: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.conversion import Conversion

        file_info = self.file_info.to_dict()

        name = self.name

        status = self.status.value

        visibility = self.visibility

        workspace_id = self.workspace_id

        conversion: Union[None, Unset, dict[str, Any]]
        if isinstance(self.conversion, Unset):
            conversion = UNSET
        elif isinstance(self.conversion, Conversion):
            conversion = self.conversion.to_dict()
        else:
            conversion = self.conversion

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

        deployed = self.deployed

        id = self.id

        image_path: Union[None, Unset, str]
        if isinstance(self.image_path, Unset):
            image_path = UNSET
        else:
            image_path = self.image_path

        task_id: Union[None, Unset, str]
        if isinstance(self.task_id, Unset):
            task_id = UNSET
        else:
            task_id = self.task_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file_info": file_info,
                "name": name,
                "status": status,
                "visibility": visibility,
                "workspace_id": workspace_id,
            }
        )
        if conversion is not UNSET:
            field_dict["conversion"] = conversion
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if created_on_version is not UNSET:
            field_dict["created_on_version"] = created_on_version
        if deployed is not UNSET:
            field_dict["deployed"] = deployed
        if id is not UNSET:
            field_dict["id"] = id
        if image_path is not UNSET:
            field_dict["image_path"] = image_path
        if task_id is not UNSET:
            field_dict["task_id"] = task_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.conversion import Conversion
        from ..models.file_info import FileInfo

        d = dict(src_dict)
        file_info = FileInfo.from_dict(d.pop("file_info"))

        name = d.pop("name")

        status = ModelStatus(d.pop("status"))

        visibility = d.pop("visibility")

        workspace_id = d.pop("workspace_id")

        def _parse_conversion(data: object) -> Union["Conversion", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                conversion_type_1 = Conversion.from_dict(data)

                return conversion_type_1
            except:  # noqa: E722
                pass
            return cast(Union["Conversion", None, Unset], data)

        conversion = _parse_conversion(d.pop("conversion", UNSET))

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

        deployed = d.pop("deployed", UNSET)

        id = d.pop("id", UNSET)

        def _parse_image_path(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        image_path = _parse_image_path(d.pop("image_path", UNSET))

        def _parse_task_id(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        task_id = _parse_task_id(d.pop("task_id", UNSET))

        model_version = cls(
            file_info=file_info,
            name=name,
            status=status,
            visibility=visibility,
            workspace_id=workspace_id,
            conversion=conversion,
            created_at=created_at,
            created_by=created_by,
            created_on_version=created_on_version,
            deployed=deployed,
            id=id,
            image_path=image_path,
            task_id=task_id,
        )

        model_version.additional_properties = d
        return model_version

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
