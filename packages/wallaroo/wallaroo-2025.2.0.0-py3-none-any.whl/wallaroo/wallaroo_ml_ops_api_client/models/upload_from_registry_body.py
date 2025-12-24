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


T = TypeVar("T", bound="UploadFromRegistryBody")


@_attrs_define
class UploadFromRegistryBody:
    """Payload for the List Registries call.

    Attributes:
        conversion (Conversion):
        name (str): A descriptive, DNS-safe name for this model in the Wallaroo system.
        path (str): The path to the model file in the remote Model Registry.
        registry_id (UUID): The unique identifier of the Model Registry in the Wallaroo system.
        visibility (str):
        workspace_id (int):
        image_path (Union[None, Unset, str]):
        input_schema (Union[None, Unset, str]):
        output_schema (Union[None, Unset, str]):
    """

    conversion: "Conversion"
    name: str
    path: str
    registry_id: UUID
    visibility: str
    workspace_id: int
    image_path: Union[None, Unset, str] = UNSET
    input_schema: Union[None, Unset, str] = UNSET
    output_schema: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        conversion = self.conversion.to_dict()

        name = self.name

        path = self.path

        registry_id = str(self.registry_id)

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "conversion": conversion,
                "name": name,
                "path": path,
                "registry_id": registry_id,
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.conversion import Conversion

        d = dict(src_dict)
        conversion = Conversion.from_dict(d.pop("conversion"))

        name = d.pop("name")

        path = d.pop("path")

        registry_id = UUID(d.pop("registry_id"))

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

        upload_from_registry_body = cls(
            conversion=conversion,
            name=name,
            path=path,
            registry_id=registry_id,
            visibility=visibility,
            workspace_id=workspace_id,
            image_path=image_path,
            input_schema=input_schema,
            output_schema=output_schema,
        )

        upload_from_registry_body.additional_properties = d
        return upload_from_registry_body

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
