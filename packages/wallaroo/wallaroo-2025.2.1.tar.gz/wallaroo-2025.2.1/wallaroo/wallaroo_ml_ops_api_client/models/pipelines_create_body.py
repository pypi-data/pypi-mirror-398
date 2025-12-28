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
    from ..models.pipelines_create_body_definition_type_0 import (
        PipelinesCreateBodyDefinitionType0,
    )


T = TypeVar("T", bound="PipelinesCreateBody")


@_attrs_define
class PipelinesCreateBody:
    """Request to create a new pipeline in a workspace.

    Attributes:
        pipeline_id (str):  Pipeline identifier.
        workspace_id (int):  Workspace identifier.
        definition (Union['PipelinesCreateBodyDefinitionType0', None, Unset]):  Pipeline definition.
    """

    pipeline_id: str
    workspace_id: int
    definition: Union["PipelinesCreateBodyDefinitionType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.pipelines_create_body_definition_type_0 import (
            PipelinesCreateBodyDefinitionType0,
        )

        pipeline_id = self.pipeline_id

        workspace_id = self.workspace_id

        definition: Union[None, Unset, dict[str, Any]]
        if isinstance(self.definition, Unset):
            definition = UNSET
        elif isinstance(self.definition, PipelinesCreateBodyDefinitionType0):
            definition = self.definition.to_dict()
        else:
            definition = self.definition

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pipeline_id": pipeline_id,
                "workspace_id": workspace_id,
            }
        )
        if definition is not UNSET:
            field_dict["definition"] = definition

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipelines_create_body_definition_type_0 import (
            PipelinesCreateBodyDefinitionType0,
        )

        d = dict(src_dict)
        pipeline_id = d.pop("pipeline_id")

        workspace_id = d.pop("workspace_id")

        def _parse_definition(
            data: object,
        ) -> Union["PipelinesCreateBodyDefinitionType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                definition_type_0 = PipelinesCreateBodyDefinitionType0.from_dict(data)

                return definition_type_0
            except:  # noqa: E722
                pass
            return cast(Union["PipelinesCreateBodyDefinitionType0", None, Unset], data)

        definition = _parse_definition(d.pop("definition", UNSET))

        pipelines_create_body = cls(
            pipeline_id=pipeline_id,
            workspace_id=workspace_id,
            definition=definition,
        )

        pipelines_create_body.additional_properties = d
        return pipelines_create_body

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
