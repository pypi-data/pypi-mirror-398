from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="Deployment")


@_attrs_define
class Deployment:
    """
    Attributes:
        maximum_replicas (int): The maximum number of replicas a deployment can scale too
        prewarmed_replicas (int): The number of instances to run, defaults to 0
    """

    maximum_replicas: int
    prewarmed_replicas: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        maximum_replicas = self.maximum_replicas

        prewarmed_replicas = self.prewarmed_replicas

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "maximum_replicas": maximum_replicas,
                "prewarmed_replicas": prewarmed_replicas,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        maximum_replicas = d.pop("maximum_replicas")

        prewarmed_replicas = d.pop("prewarmed_replicas")

        deployment = cls(
            maximum_replicas=maximum_replicas,
            prewarmed_replicas=prewarmed_replicas,
        )

        deployment.additional_properties = d
        return deployment

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
