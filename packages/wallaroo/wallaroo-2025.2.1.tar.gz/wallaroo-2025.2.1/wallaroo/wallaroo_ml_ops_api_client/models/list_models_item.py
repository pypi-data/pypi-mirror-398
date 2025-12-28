from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.configured_model_version import ConfiguredModelVersion
    from ..models.model import Model
    from ..models.workspace import Workspace


T = TypeVar("T", bound="ListModelsItem")


@_attrs_define
class ListModelsItem:
    """
    Attributes:
        model (Model):
        model_versions (list['ConfiguredModelVersion']):
        workspace (Workspace):
    """

    model: "Model"
    model_versions: list["ConfiguredModelVersion"]
    workspace: "Workspace"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        model = self.model.to_dict()

        model_versions = []
        for model_versions_item_data in self.model_versions:
            model_versions_item = model_versions_item_data.to_dict()
            model_versions.append(model_versions_item)

        workspace = self.workspace.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "model": model,
                "model_versions": model_versions,
                "workspace": workspace,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.configured_model_version import ConfiguredModelVersion
        from ..models.model import Model
        from ..models.workspace import Workspace

        d = dict(src_dict)
        model = Model.from_dict(d.pop("model"))

        model_versions = []
        _model_versions = d.pop("model_versions")
        for model_versions_item_data in _model_versions:
            model_versions_item = ConfiguredModelVersion.from_dict(
                model_versions_item_data
            )

            model_versions.append(model_versions_item)

        workspace = Workspace.from_dict(d.pop("workspace"))

        list_models_item = cls(
            model=model,
            model_versions=model_versions,
            workspace=workspace,
        )

        list_models_item.additional_properties = d
        return list_models_item

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
