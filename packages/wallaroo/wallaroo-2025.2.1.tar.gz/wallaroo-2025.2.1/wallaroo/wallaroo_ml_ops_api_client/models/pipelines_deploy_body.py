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
    from ..models.model_version_stub import ModelVersionStub


T = TypeVar("T", bound="PipelinesDeployBody")


@_attrs_define
class PipelinesDeployBody:
    """Pipeline deployment request.

    Attributes:
        deploy_id (str): Deployment identifier.
        engine_config (Union[Unset, Any]): Optional engine configuration.
        model_configs (Union[None, Unset, list[int]]): Optional model configurations.
        model_ids (Union[None, Unset, list[int]]): Optional model identifiers.
            If model_ids are passed in, we will create model_configs for them.
        models (Union[None, Unset, list['ModelVersionStub']]): Optional model.
            Because model_ids may not be readily available for existing pipelines, they can pass in all the data again.
        pipeline_id (Union[None, Unset, int]): Pipeline identifier.
        pipeline_version (Union[None, UUID, Unset]): Optional pipeline version identifier.
        pipeline_version_pk_id (Union[None, Unset, int]): Internal pipeline version identifier.
    """

    deploy_id: str
    engine_config: Union[Unset, Any] = UNSET
    model_configs: Union[None, Unset, list[int]] = UNSET
    model_ids: Union[None, Unset, list[int]] = UNSET
    models: Union[None, Unset, list["ModelVersionStub"]] = UNSET
    pipeline_id: Union[None, Unset, int] = UNSET
    pipeline_version: Union[None, UUID, Unset] = UNSET
    pipeline_version_pk_id: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        deploy_id = self.deploy_id

        engine_config = self.engine_config

        model_configs: Union[None, Unset, list[int]]
        if isinstance(self.model_configs, Unset):
            model_configs = UNSET
        elif isinstance(self.model_configs, list):
            model_configs = self.model_configs

        else:
            model_configs = self.model_configs

        model_ids: Union[None, Unset, list[int]]
        if isinstance(self.model_ids, Unset):
            model_ids = UNSET
        elif isinstance(self.model_ids, list):
            model_ids = self.model_ids

        else:
            model_ids = self.model_ids

        models: Union[None, Unset, list[dict[str, Any]]]
        if isinstance(self.models, Unset):
            models = UNSET
        elif isinstance(self.models, list):
            models = []
            for models_type_0_item_data in self.models:
                models_type_0_item = models_type_0_item_data.to_dict()
                models.append(models_type_0_item)

        else:
            models = self.models

        pipeline_id: Union[None, Unset, int]
        if isinstance(self.pipeline_id, Unset):
            pipeline_id = UNSET
        else:
            pipeline_id = self.pipeline_id

        pipeline_version: Union[None, Unset, str]
        if isinstance(self.pipeline_version, Unset):
            pipeline_version = UNSET
        elif isinstance(self.pipeline_version, UUID):
            pipeline_version = str(self.pipeline_version)
        else:
            pipeline_version = self.pipeline_version

        pipeline_version_pk_id: Union[None, Unset, int]
        if isinstance(self.pipeline_version_pk_id, Unset):
            pipeline_version_pk_id = UNSET
        else:
            pipeline_version_pk_id = self.pipeline_version_pk_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "deploy_id": deploy_id,
            }
        )
        if engine_config is not UNSET:
            field_dict["engine_config"] = engine_config
        if model_configs is not UNSET:
            field_dict["model_configs"] = model_configs
        if model_ids is not UNSET:
            field_dict["model_ids"] = model_ids
        if models is not UNSET:
            field_dict["models"] = models
        if pipeline_id is not UNSET:
            field_dict["pipeline_id"] = pipeline_id
        if pipeline_version is not UNSET:
            field_dict["pipeline_version"] = pipeline_version
        if pipeline_version_pk_id is not UNSET:
            field_dict["pipeline_version_pk_id"] = pipeline_version_pk_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.model_version_stub import ModelVersionStub

        d = dict(src_dict)
        deploy_id = d.pop("deploy_id")

        engine_config = d.pop("engine_config", UNSET)

        def _parse_model_configs(data: object) -> Union[None, Unset, list[int]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                model_configs_type_0 = cast(list[int], data)

                return model_configs_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[int]], data)

        model_configs = _parse_model_configs(d.pop("model_configs", UNSET))

        def _parse_model_ids(data: object) -> Union[None, Unset, list[int]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                model_ids_type_0 = cast(list[int], data)

                return model_ids_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[int]], data)

        model_ids = _parse_model_ids(d.pop("model_ids", UNSET))

        def _parse_models(data: object) -> Union[None, Unset, list["ModelVersionStub"]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                models_type_0 = []
                _models_type_0 = data
                for models_type_0_item_data in _models_type_0:
                    models_type_0_item = ModelVersionStub.from_dict(
                        models_type_0_item_data
                    )

                    models_type_0.append(models_type_0_item)

                return models_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list["ModelVersionStub"]], data)

        models = _parse_models(d.pop("models", UNSET))

        def _parse_pipeline_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pipeline_id = _parse_pipeline_id(d.pop("pipeline_id", UNSET))

        def _parse_pipeline_version(data: object) -> Union[None, UUID, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                pipeline_version_type_0 = UUID(data)

                return pipeline_version_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, UUID, Unset], data)

        pipeline_version = _parse_pipeline_version(d.pop("pipeline_version", UNSET))

        def _parse_pipeline_version_pk_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pipeline_version_pk_id = _parse_pipeline_version_pk_id(
            d.pop("pipeline_version_pk_id", UNSET)
        )

        pipelines_deploy_body = cls(
            deploy_id=deploy_id,
            engine_config=engine_config,
            model_configs=model_configs,
            model_ids=model_ids,
            models=models,
            pipeline_id=pipeline_id,
            pipeline_version=pipeline_version,
            pipeline_version_pk_id=pipeline_version_pk_id,
        )

        pipelines_deploy_body.additional_properties = d
        return pipelines_deploy_body

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
