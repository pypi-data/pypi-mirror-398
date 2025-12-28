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

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.conversion import Conversion


T = TypeVar("T", bound="UploadRequest")


@_attrs_define
class UploadRequest:
    """
    Attributes:
        conversion (Conversion):
        name (str):
        visibility (str):
        workspace_id (int):
        image_path (Union[None, Unset, str]):
        input_schema (Union[None, Unset, str]):
        output_schema (Union[None, Unset, str]):
        registry_id (Union[None, UUID, Unset]): The unique identifier for a Registry
            Not compatible with file uploads, only used with `registry_uri` uploads
    """

    conversion: "Conversion"
    name: str
    visibility: str
    workspace_id: int
    image_path: Union[None, Unset, str] = UNSET
    input_schema: Union[None, Unset, str] = UNSET
    output_schema: Union[None, Unset, str] = UNSET
    registry_id: Union[None, UUID, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        conversion = self.conversion.to_dict()

        name = self.name

        visibility = self.visibility

        workspace_id = self.workspace_id

        image_path: Union[None, Unset, str]
        if isinstance(self.image_path, Unset):
            image_path = UNSET
        else:
            image_path = self.image_path

        input_schema: Union[None, Unset, str]
        if isinstance(self.input_schema, Unset):
            input_schema = UNSET
        else:
            input_schema = self.input_schema

        output_schema: Union[None, Unset, str]
        if isinstance(self.output_schema, Unset):
            output_schema = UNSET
        else:
            output_schema = self.output_schema

        registry_id: Union[None, Unset, str]
        if isinstance(self.registry_id, Unset):
            registry_id = UNSET
        elif isinstance(self.registry_id, UUID):
            registry_id = str(self.registry_id)
        else:
            registry_id = self.registry_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "conversion": conversion,
                "name": name,
                "visibility": visibility,
                "workspace_id": workspace_id,
            }
        )
        if image_path is not UNSET:
            field_dict["image_path"] = image_path
        if input_schema is not UNSET:
            field_dict["input_schema"] = input_schema
        if output_schema is not UNSET:
            field_dict["output_schema"] = output_schema
        if registry_id is not UNSET:
            field_dict["registry_id"] = registry_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.conversion import Conversion

        d = dict(src_dict)
        conversion = Conversion.from_dict(d.pop("conversion"))

        name = d.pop("name")

        visibility = d.pop("visibility")

        workspace_id = d.pop("workspace_id")

        def _parse_image_path(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        image_path = _parse_image_path(d.pop("image_path", UNSET))

        def _parse_input_schema(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        input_schema = _parse_input_schema(d.pop("input_schema", UNSET))

        def _parse_output_schema(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        output_schema = _parse_output_schema(d.pop("output_schema", UNSET))

        def _parse_registry_id(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                registry_id_type_0 = UUID(data)

                return registry_id_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        registry_id = _parse_registry_id(d.pop("registry_id", UNSET))

        upload_request = cls(
            conversion=conversion,
            name=name,
            visibility=visibility,
            workspace_id=workspace_id,
            image_path=image_path,
            input_schema=input_schema,
            output_schema=output_schema,
            registry_id=registry_id,
        )

        upload_request.additional_properties = d
        return upload_request

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
