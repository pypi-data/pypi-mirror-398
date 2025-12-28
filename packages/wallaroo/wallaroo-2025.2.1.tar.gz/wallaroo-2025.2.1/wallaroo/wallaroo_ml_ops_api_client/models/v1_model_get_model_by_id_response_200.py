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
    from ..models.v1_model_get_model_by_id_response_200_model_config_type_0 import (
        V1ModelGetModelByIdResponse200ModelConfigType0,
    )


T = TypeVar("T", bound="V1ModelGetModelByIdResponse200")


@_attrs_define
class V1ModelGetModelByIdResponse200:
    """Response type for /models/get_by_id

    Attributes:
        id (int):  The primary model ID
        owner_id (str):  The user id who created and owns the model.
        name (str):  The name of the model.
        workspace_id (Union[None, Unset, int]):  Workspace Primary id, which the model belongs too.
        updated_at (Union[None, Unset, str]):  When the model was last updated.
        created_at (Union[None, Unset, str]):  When the model was first created.
        model_config (Union['V1ModelGetModelByIdResponse200ModelConfigType0', None, Unset]):  A possible Model
            Configuration
    """

    id: int
    owner_id: str
    name: str
    workspace_id: Union[None, Unset, int] = UNSET
    updated_at: Union[None, Unset, str] = UNSET
    created_at: Union[None, Unset, str] = UNSET
    model_config: Union[
        "V1ModelGetModelByIdResponse200ModelConfigType0", None, Unset
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.v1_model_get_model_by_id_response_200_model_config_type_0 import (
            V1ModelGetModelByIdResponse200ModelConfigType0,
        )

        id = self.id

        owner_id = self.owner_id

        name = self.name

        workspace_id: Union[None, Unset, int]
        if isinstance(self.workspace_id, Unset):
            workspace_id = UNSET
        else:
            workspace_id = self.workspace_id

        updated_at: Union[None, Unset, str]
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = self.updated_at

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        model_config: Union[None, Unset, dict[str, Any]]
        if isinstance(self.model_config, Unset):
            model_config = UNSET
        elif isinstance(
            self.model_config, V1ModelGetModelByIdResponse200ModelConfigType0
        ):
            model_config = self.model_config.to_dict()
        else:
            model_config = self.model_config

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "owner_id": owner_id,
                "name": name,
            }
        )
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if model_config is not UNSET:
            field_dict["model_config"] = model_config

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.v1_model_get_model_by_id_response_200_model_config_type_0 import (
            V1ModelGetModelByIdResponse200ModelConfigType0,
        )

        d = dict(src_dict)
        id = d.pop("id")

        owner_id = d.pop("owner_id")

        name = d.pop("name")

        def _parse_workspace_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        workspace_id = _parse_workspace_id(d.pop("workspace_id", UNSET))

        def _parse_updated_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        def _parse_created_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_model_config(
            data: object,
        ) -> Union["V1ModelGetModelByIdResponse200ModelConfigType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                model_config_type_0 = (
                    V1ModelGetModelByIdResponse200ModelConfigType0.from_dict(data)
                )

                return model_config_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["V1ModelGetModelByIdResponse200ModelConfigType0", None, Unset],
                data,
            )

        model_config = _parse_model_config(d.pop("model_config", UNSET))

        v1_model_get_model_by_id_response_200 = cls(
            id=id,
            owner_id=owner_id,
            name=name,
            workspace_id=workspace_id,
            updated_at=updated_at,
            created_at=created_at,
            model_config=model_config,
        )

        v1_model_get_model_by_id_response_200.additional_properties = d
        return v1_model_get_model_by_id_response_200

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
