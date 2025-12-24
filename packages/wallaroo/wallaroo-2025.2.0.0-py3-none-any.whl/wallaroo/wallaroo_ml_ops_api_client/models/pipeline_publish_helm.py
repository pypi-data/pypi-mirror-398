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
    from ..models.pipeline_publish_helm_values import PipelinePublishHelmValues


T = TypeVar("T", bound="PipelinePublishHelm")


@_attrs_define
class PipelinePublishHelm:
    """
    Attributes:
        reference (str):
        values (PipelinePublishHelmValues):
        chart (Union[None, Unset, str]):
        version (Union[None, Unset, str]):
    """

    reference: str
    values: "PipelinePublishHelmValues"
    chart: Union[None, Unset, str] = UNSET
    version: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        reference = self.reference

        values = self.values.to_dict()

        chart: Union[None, Unset, str]
        if isinstance(self.chart, Unset):
            chart = UNSET
        else:
            chart = self.chart

        version: Union[None, Unset, str]
        if isinstance(self.version, Unset):
            version = UNSET
        else:
            version = self.version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "reference": reference,
                "values": values,
            }
        )
        if chart is not UNSET:
            field_dict["chart"] = chart
        if version is not UNSET:
            field_dict["version"] = version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pipeline_publish_helm_values import PipelinePublishHelmValues

        d = dict(src_dict)
        reference = d.pop("reference")

        values = PipelinePublishHelmValues.from_dict(d.pop("values"))

        def _parse_chart(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        chart = _parse_chart(d.pop("chart", UNSET))

        def _parse_version(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        version = _parse_version(d.pop("version", UNSET))

        pipeline_publish_helm = cls(
            reference=reference,
            values=values,
            chart=chart,
            version=version,
        )

        pipeline_publish_helm.additional_properties = d
        return pipeline_publish_helm

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
