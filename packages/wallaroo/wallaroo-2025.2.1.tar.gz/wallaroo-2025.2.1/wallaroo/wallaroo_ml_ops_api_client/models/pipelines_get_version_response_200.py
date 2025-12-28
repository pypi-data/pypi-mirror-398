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
    from ..models.pipelines_get_version_response_200_definition_type_0 import (
        PipelinesGetVersionResponse200DefinitionType0,
    )


T = TypeVar("T", bound="PipelinesGetVersionResponse200")


@_attrs_define
class PipelinesGetVersionResponse200:
    """
    Attributes:
        pipeline_id (str):
        version (str):
        definition (Union['PipelinesGetVersionResponse200DefinitionType0', None, Unset]):
    """

    pipeline_id: str
    version: str
    definition: Union["PipelinesGetVersionResponse200DefinitionType0", None, Unset] = (
        UNSET
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.pipelines_get_version_response_200_definition_type_0 import (
            PipelinesGetVersionResponse200DefinitionType0,
        )

        pipeline_id = self.pipeline_id

        version = self.version

        definition: Union[None, Unset, dict[str, Any]]
        if isinstance(self.definition, Unset):
            definition = UNSET
        elif isinstance(self.definition, PipelinesGetVersionResponse200DefinitionType0):
            definition = self.definition.to_dict()
        else:
            definition = self.definition

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pipeline_id": pipeline_id,
                "version": version,
            }
        )
        if definition is not UNSET:
            field_dict["definition"] = definition

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipelines_get_version_response_200_definition_type_0 import (
            PipelinesGetVersionResponse200DefinitionType0,
        )

        d = dict(src_dict)
        pipeline_id = d.pop("pipeline_id")

        version = d.pop("version")

        def _parse_definition(
            data: object,
        ) -> Union["PipelinesGetVersionResponse200DefinitionType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                definition_type_0 = (
                    PipelinesGetVersionResponse200DefinitionType0.from_dict(data)
                )

                return definition_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["PipelinesGetVersionResponse200DefinitionType0", None, Unset],
                data,
            )

        definition = _parse_definition(d.pop("definition", UNSET))

        pipelines_get_version_response_200 = cls(
            pipeline_id=pipeline_id,
            version=version,
            definition=definition,
        )

        pipelines_get_version_response_200.additional_properties = d
        return pipelines_get_version_response_200

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
