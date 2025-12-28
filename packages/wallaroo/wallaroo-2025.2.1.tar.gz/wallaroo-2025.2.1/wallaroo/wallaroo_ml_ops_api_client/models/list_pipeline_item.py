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
    from ..models.deployment import Deployment
    from ..models.legacy_pipeline_version import LegacyPipelineVersion
    from ..models.pipeline import Pipeline
    from ..models.workspace import Workspace


T = TypeVar("T", bound="ListPipelineItem")


@_attrs_define
class ListPipelineItem:
    """Response with a list of published pipelines.

    Attributes:
        pipeline (Pipeline): Definition of an inference pipeline that can be deployed on the edge.
        plateau_topic (str):
        workspace (Workspace):
        deployment (Union['Deployment', None, Unset]):
        pipeline_version (Union['LegacyPipelineVersion', None, Unset]):
    """

    pipeline: "Pipeline"
    plateau_topic: str
    workspace: "Workspace"
    deployment: Union["Deployment", None, Unset] = UNSET
    pipeline_version: Union["LegacyPipelineVersion", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.deployment import Deployment
        from ..models.legacy_pipeline_version import LegacyPipelineVersion

        pipeline = self.pipeline.to_dict()

        plateau_topic = self.plateau_topic

        workspace = self.workspace.to_dict()

        deployment: Union[None, Unset, dict[str, Any]]
        if isinstance(self.deployment, Unset):
            deployment = UNSET
        elif isinstance(self.deployment, Deployment):
            deployment = self.deployment.to_dict()
        else:
            deployment = self.deployment

        pipeline_version: Union[None, Unset, dict[str, Any]]
        if isinstance(self.pipeline_version, Unset):
            pipeline_version = UNSET
        elif isinstance(self.pipeline_version, LegacyPipelineVersion):
            pipeline_version = self.pipeline_version.to_dict()
        else:
            pipeline_version = self.pipeline_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pipeline": pipeline,
                "plateau_topic": plateau_topic,
                "workspace": workspace,
            }
        )
        if deployment is not UNSET:
            field_dict["deployment"] = deployment
        if pipeline_version is not UNSET:
            field_dict["pipeline_version"] = pipeline_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deployment import Deployment
        from ..models.legacy_pipeline_version import LegacyPipelineVersion
        from ..models.pipeline import Pipeline
        from ..models.workspace import Workspace

        d = dict(src_dict)
        pipeline = Pipeline.from_dict(d.pop("pipeline"))

        plateau_topic = d.pop("plateau_topic")

        workspace = Workspace.from_dict(d.pop("workspace"))

        def _parse_deployment(data: object) -> Union["Deployment", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                deployment_type_1 = Deployment.from_dict(data)

                return deployment_type_1
            except:  # noqa: E722
                pass
            return cast(Union["Deployment", None, Unset], data)

        deployment = _parse_deployment(d.pop("deployment", UNSET))

        def _parse_pipeline_version(
            data: object,
        ) -> Union["LegacyPipelineVersion", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                pipeline_version_type_1 = LegacyPipelineVersion.from_dict(data)

                return pipeline_version_type_1
            except:  # noqa: E722
                pass
            return cast(Union["LegacyPipelineVersion", None, Unset], data)

        pipeline_version = _parse_pipeline_version(d.pop("pipeline_version", UNSET))

        list_pipeline_item = cls(
            pipeline=pipeline,
            plateau_topic=plateau_topic,
            workspace=workspace,
            deployment=deployment,
            pipeline_version=pipeline_version,
        )

        list_pipeline_item.additional_properties = d
        return list_pipeline_item

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
