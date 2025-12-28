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
    from ..models.status_get_deployment_response_200_engines_item_info import (
        StatusGetDeploymentResponse200EnginesItemInfo,
    )
    from ..models.status_get_deployment_response_200_engines_item_model_statuses_type_0 import (
        StatusGetDeploymentResponse200EnginesItemModelStatusesType0,
    )
    from ..models.status_get_deployment_response_200_engines_item_pipeline_statuses_type_0 import (
        StatusGetDeploymentResponse200EnginesItemPipelineStatusesType0,
    )


T = TypeVar("T", bound="StatusGetDeploymentResponse200EnginesItem")


@_attrs_define
class StatusGetDeploymentResponse200EnginesItem:
    """Engine deployment status.

    Attributes:
        info (StatusGetDeploymentResponse200EnginesItemInfo):
        pipeline_statuses (Union['StatusGetDeploymentResponse200EnginesItemPipelineStatusesType0', None, Unset]):
            Statuses of pipelines serviced by the engine.
        model_statuses (Union['StatusGetDeploymentResponse200EnginesItemModelStatusesType0', None, Unset]):  Statuses of
            models executed by the engine.
    """

    info: "StatusGetDeploymentResponse200EnginesItemInfo"
    pipeline_statuses: Union[
        "StatusGetDeploymentResponse200EnginesItemPipelineStatusesType0", None, Unset
    ] = UNSET
    model_statuses: Union[
        "StatusGetDeploymentResponse200EnginesItemModelStatusesType0", None, Unset
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.status_get_deployment_response_200_engines_item_model_statuses_type_0 import (
            StatusGetDeploymentResponse200EnginesItemModelStatusesType0,
        )
        from ..models.status_get_deployment_response_200_engines_item_pipeline_statuses_type_0 import (
            StatusGetDeploymentResponse200EnginesItemPipelineStatusesType0,
        )

        info = self.info.to_dict()

        pipeline_statuses: Union[None, Unset, dict[str, Any]]
        if isinstance(self.pipeline_statuses, Unset):
            pipeline_statuses = UNSET
        elif isinstance(
            self.pipeline_statuses,
            StatusGetDeploymentResponse200EnginesItemPipelineStatusesType0,
        ):
            pipeline_statuses = self.pipeline_statuses.to_dict()
        else:
            pipeline_statuses = self.pipeline_statuses

        model_statuses: Union[None, Unset, dict[str, Any]]
        if isinstance(self.model_statuses, Unset):
            model_statuses = UNSET
        elif isinstance(
            self.model_statuses,
            StatusGetDeploymentResponse200EnginesItemModelStatusesType0,
        ):
            model_statuses = self.model_statuses.to_dict()
        else:
            model_statuses = self.model_statuses

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "info": info,
            }
        )
        if pipeline_statuses is not UNSET:
            field_dict["pipeline_statuses"] = pipeline_statuses
        if model_statuses is not UNSET:
            field_dict["model_statuses"] = model_statuses

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.status_get_deployment_response_200_engines_item_info import (
            StatusGetDeploymentResponse200EnginesItemInfo,
        )
        from ..models.status_get_deployment_response_200_engines_item_model_statuses_type_0 import (
            StatusGetDeploymentResponse200EnginesItemModelStatusesType0,
        )
        from ..models.status_get_deployment_response_200_engines_item_pipeline_statuses_type_0 import (
            StatusGetDeploymentResponse200EnginesItemPipelineStatusesType0,
        )

        d = dict(src_dict)
        info = StatusGetDeploymentResponse200EnginesItemInfo.from_dict(d.pop("info"))

        def _parse_pipeline_statuses(
            data: object,
        ) -> Union[
            "StatusGetDeploymentResponse200EnginesItemPipelineStatusesType0",
            None,
            Unset,
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                pipeline_statuses_type_0 = StatusGetDeploymentResponse200EnginesItemPipelineStatusesType0.from_dict(
                    data
                )

                return pipeline_statuses_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "StatusGetDeploymentResponse200EnginesItemPipelineStatusesType0",
                    None,
                    Unset,
                ],
                data,
            )

        pipeline_statuses = _parse_pipeline_statuses(d.pop("pipeline_statuses", UNSET))

        def _parse_model_statuses(
            data: object,
        ) -> Union[
            "StatusGetDeploymentResponse200EnginesItemModelStatusesType0", None, Unset
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                model_statuses_type_0 = StatusGetDeploymentResponse200EnginesItemModelStatusesType0.from_dict(
                    data
                )

                return model_statuses_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "StatusGetDeploymentResponse200EnginesItemModelStatusesType0",
                    None,
                    Unset,
                ],
                data,
            )

        model_statuses = _parse_model_statuses(d.pop("model_statuses", UNSET))

        status_get_deployment_response_200_engines_item = cls(
            info=info,
            pipeline_statuses=pipeline_statuses,
            model_statuses=model_statuses,
        )

        status_get_deployment_response_200_engines_item.additional_properties = d
        return status_get_deployment_response_200_engines_item

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
