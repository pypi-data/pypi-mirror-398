import datetime
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
from dateutil.parser import isoparse

from ..models.app_version import AppVersion
from ..models.pipeline_publish_status import PipelinePublishStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.engine_config import EngineConfig
    from ..models.old_publish import OldPublish
    from ..models.pipeline_publish_docker_run_variables import (
        PipelinePublishDockerRunVariables,
    )
    from ..models.pipeline_publish_edge_bundles import PipelinePublishEdgeBundles
    from ..models.pipeline_publish_helm import PipelinePublishHelm


T = TypeVar("T", bound="PipelinePublish")


@_attrs_define
class PipelinePublish:
    """
    Attributes:
        created_at (datetime.datetime):
        docker_run_variables (PipelinePublishDockerRunVariables):
        engine_config (EngineConfig):
        id (int):
        pipeline_name (str):
        pipeline_version_id (int):
        replaces (list['OldPublish']):
        status (PipelinePublishStatus):
        updated_at (datetime.datetime):
        user_images (list[str]):
        created_by (Union[None, Unset, str]):
        created_on_version (Union[Unset, AppVersion]):
        edge_bundles (Union[Unset, PipelinePublishEdgeBundles]):
        engine_url (Union[None, Unset, str]):
        error (Union[None, Unset, str]): If [PipelinePublish::status] is in the [PipelinePublishStatus::Error] state,
            this should be populated with the error that occurred.
        helm (Union['PipelinePublishHelm', None, Unset]):
        pipeline_url (Union[None, Unset, str]):
        pipeline_version_name (Union[None, UUID, Unset]):
        workspace_id (Union[None, Unset, int]):
        workspace_name (Union[None, Unset, str]):
    """

    created_at: datetime.datetime
    docker_run_variables: "PipelinePublishDockerRunVariables"
    engine_config: "EngineConfig"
    id: int
    pipeline_name: str
    pipeline_version_id: int
    replaces: list["OldPublish"]
    status: PipelinePublishStatus
    updated_at: datetime.datetime
    user_images: list[str]
    created_by: Union[None, Unset, str] = UNSET
    created_on_version: Union[Unset, AppVersion] = UNSET
    edge_bundles: Union[Unset, "PipelinePublishEdgeBundles"] = UNSET
    engine_url: Union[None, Unset, str] = UNSET
    error: Union[None, Unset, str] = UNSET
    helm: Union["PipelinePublishHelm", None, Unset] = UNSET
    pipeline_url: Union[None, Unset, str] = UNSET
    pipeline_version_name: Union[None, UUID, Unset] = UNSET
    workspace_id: Union[None, Unset, int] = UNSET
    workspace_name: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.pipeline_publish_helm import PipelinePublishHelm

        created_at = self.created_at.isoformat()

        docker_run_variables = self.docker_run_variables.to_dict()

        engine_config = self.engine_config.to_dict()

        id = self.id

        pipeline_name = self.pipeline_name

        pipeline_version_id = self.pipeline_version_id

        replaces = []
        for replaces_item_data in self.replaces:
            replaces_item = replaces_item_data.to_dict()
            replaces.append(replaces_item)

        status = self.status.value

        updated_at = self.updated_at.isoformat()

        user_images = self.user_images

        created_by: Union[None, Unset, str]
        if isinstance(self.created_by, Unset):
            created_by = UNSET
        else:
            created_by = self.created_by

        created_on_version: Union[Unset, str] = UNSET
        if not isinstance(self.created_on_version, Unset):
            created_on_version = self.created_on_version.value

        edge_bundles: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.edge_bundles, Unset):
            edge_bundles = self.edge_bundles.to_dict()

        engine_url: Union[None, Unset, str]
        if isinstance(self.engine_url, Unset):
            engine_url = UNSET
        else:
            engine_url = self.engine_url

        error: Union[None, Unset, str]
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        helm: Union[None, Unset, dict[str, Any]]
        if isinstance(self.helm, Unset):
            helm = UNSET
        elif isinstance(self.helm, PipelinePublishHelm):
            helm = self.helm.to_dict()
        else:
            helm = self.helm

        pipeline_url: Union[None, Unset, str]
        if isinstance(self.pipeline_url, Unset):
            pipeline_url = UNSET
        else:
            pipeline_url = self.pipeline_url

        pipeline_version_name: Union[None, Unset, str]
        if isinstance(self.pipeline_version_name, Unset):
            pipeline_version_name = UNSET
        elif isinstance(self.pipeline_version_name, UUID):
            pipeline_version_name = str(self.pipeline_version_name)
        else:
            pipeline_version_name = self.pipeline_version_name

        workspace_id: Union[None, Unset, int]
        if isinstance(self.workspace_id, Unset):
            workspace_id = UNSET
        else:
            workspace_id = self.workspace_id

        workspace_name: Union[None, Unset, str]
        if isinstance(self.workspace_name, Unset):
            workspace_name = UNSET
        else:
            workspace_name = self.workspace_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "created_at": created_at,
                "docker_run_variables": docker_run_variables,
                "engine_config": engine_config,
                "id": id,
                "pipeline_name": pipeline_name,
                "pipeline_version_id": pipeline_version_id,
                "replaces": replaces,
                "status": status,
                "updated_at": updated_at,
                "user_images": user_images,
            }
        )
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if created_on_version is not UNSET:
            field_dict["created_on_version"] = created_on_version
        if edge_bundles is not UNSET:
            field_dict["edge_bundles"] = edge_bundles
        if engine_url is not UNSET:
            field_dict["engine_url"] = engine_url
        if error is not UNSET:
            field_dict["error"] = error
        if helm is not UNSET:
            field_dict["helm"] = helm
        if pipeline_url is not UNSET:
            field_dict["pipeline_url"] = pipeline_url
        if pipeline_version_name is not UNSET:
            field_dict["pipeline_version_name"] = pipeline_version_name
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id
        if workspace_name is not UNSET:
            field_dict["workspace_name"] = workspace_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.engine_config import EngineConfig
        from ..models.old_publish import OldPublish
        from ..models.pipeline_publish_docker_run_variables import (
            PipelinePublishDockerRunVariables,
        )
        from ..models.pipeline_publish_edge_bundles import PipelinePublishEdgeBundles
        from ..models.pipeline_publish_helm import PipelinePublishHelm

        d = dict(src_dict)
        created_at = isoparse(d.pop("created_at"))

        docker_run_variables = PipelinePublishDockerRunVariables.from_dict(
            d.pop("docker_run_variables")
        )

        engine_config = EngineConfig.from_dict(d.pop("engine_config"))

        id = d.pop("id")

        pipeline_name = d.pop("pipeline_name")

        pipeline_version_id = d.pop("pipeline_version_id")

        replaces = []
        _replaces = d.pop("replaces")
        for replaces_item_data in _replaces:
            replaces_item = OldPublish.from_dict(replaces_item_data)

            replaces.append(replaces_item)

        status = PipelinePublishStatus(d.pop("status"))

        updated_at = isoparse(d.pop("updated_at"))

        user_images = cast(list[str], d.pop("user_images"))

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

        _edge_bundles = d.pop("edge_bundles", UNSET)
        edge_bundles: Union[Unset, PipelinePublishEdgeBundles]
        if isinstance(_edge_bundles, Unset):
            edge_bundles = UNSET
        else:
            edge_bundles = PipelinePublishEdgeBundles.from_dict(_edge_bundles)

        def _parse_engine_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        engine_url = _parse_engine_url(d.pop("engine_url", UNSET))

        def _parse_error(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        error = _parse_error(d.pop("error", UNSET))

        def _parse_helm(data: object) -> Union["PipelinePublishHelm", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                helm_type_1 = PipelinePublishHelm.from_dict(data)

                return helm_type_1
            except:  # noqa: E722
                pass
            return cast(Union["PipelinePublishHelm", None, Unset], data)

        helm = _parse_helm(d.pop("helm", UNSET))

        def _parse_pipeline_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        pipeline_url = _parse_pipeline_url(d.pop("pipeline_url", UNSET))

        def _parse_pipeline_version_name(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                pipeline_version_name_type_0 = UUID(data)

                return pipeline_version_name_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        pipeline_version_name = _parse_pipeline_version_name(
            d.pop("pipeline_version_name", UNSET)
        )

        def _parse_workspace_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        workspace_id = _parse_workspace_id(d.pop("workspace_id", UNSET))

        def _parse_workspace_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        workspace_name = _parse_workspace_name(d.pop("workspace_name", UNSET))

        pipeline_publish = cls(
            created_at=created_at,
            docker_run_variables=docker_run_variables,
            engine_config=engine_config,
            id=id,
            pipeline_name=pipeline_name,
            pipeline_version_id=pipeline_version_id,
            replaces=replaces,
            status=status,
            updated_at=updated_at,
            user_images=user_images,
            created_by=created_by,
            created_on_version=created_on_version,
            edge_bundles=edge_bundles,
            engine_url=engine_url,
            error=error,
            helm=helm,
            pipeline_url=pipeline_url,
            pipeline_version_name=pipeline_version_name,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
        )

        pipeline_publish.additional_properties = d
        return pipeline_publish

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
