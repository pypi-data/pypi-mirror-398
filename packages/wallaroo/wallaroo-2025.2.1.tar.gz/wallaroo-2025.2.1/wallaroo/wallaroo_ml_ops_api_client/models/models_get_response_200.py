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
    from ..models.models_get_response_200_models_item import (
        ModelsGetResponse200ModelsItem,
    )
    from ..models.models_get_response_200_workspace import ModelsGetResponse200Workspace


T = TypeVar("T", bound="ModelsGetResponse200")


@_attrs_define
class ModelsGetResponse200:
    """Successful response to workspace model retrieval.  Details for a single Models object in the workspace.

    Attributes:
        id (int):  Model identifer.
        name (str):  The descriptive name of the model, the same as `model_id`.
        owner_id (str):  The UUID of the User.
        models (list['ModelsGetResponse200ModelsItem']):
        workspace (ModelsGetResponse200Workspace):  Workspace details.
        created_at (Union[None, Unset, str]):  The timestamp that this model was created.
        updated_at (Union[None, Unset, str]):  The last time this model object was updated.
    """

    id: int
    name: str
    owner_id: str
    models: list["ModelsGetResponse200ModelsItem"]
    workspace: "ModelsGetResponse200Workspace"
    created_at: Union[None, Unset, str] = UNSET
    updated_at: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        owner_id = self.owner_id

        models = []
        for models_item_data in self.models:
            models_item = models_item_data.to_dict()
            models.append(models_item)

        workspace = self.workspace.to_dict()

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        updated_at: Union[None, Unset, str]
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = self.updated_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "owner_id": owner_id,
                "models": models,
                "workspace": workspace,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.models_get_response_200_models_item import (
            ModelsGetResponse200ModelsItem,
        )
        from ..models.models_get_response_200_workspace import (
            ModelsGetResponse200Workspace,
        )

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        owner_id = d.pop("owner_id")

        models = []
        _models = d.pop("models")
        for models_item_data in _models:
            models_item = ModelsGetResponse200ModelsItem.from_dict(models_item_data)

            models.append(models_item)

        workspace = ModelsGetResponse200Workspace.from_dict(d.pop("workspace"))

        def _parse_created_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_updated_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        models_get_response_200 = cls(
            id=id,
            name=name,
            owner_id=owner_id,
            models=models,
            workspace=workspace,
            created_at=created_at,
            updated_at=updated_at,
        )

        models_get_response_200.additional_properties = d
        return models_get_response_200

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
