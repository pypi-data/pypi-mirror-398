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
    from ..models.resources_spec import ResourcesSpec


T = TypeVar("T", bound="Resources")


@_attrs_define
class Resources:
    """
    Attributes:
        resources (Union['ResourcesSpec', None, Unset]):
    """

    resources: Union["ResourcesSpec", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.resources_spec import ResourcesSpec

        resources: Union[None, Unset, dict[str, Any]]
        if isinstance(self.resources, Unset):
            resources = UNSET
        elif isinstance(self.resources, ResourcesSpec):
            resources = self.resources.to_dict()
        else:
            resources = self.resources

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if resources is not UNSET:
            field_dict["resources"] = resources

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.resources_spec import ResourcesSpec

        d = dict(src_dict)

        def _parse_resources(data: object) -> Union["ResourcesSpec", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                resources_type_1 = ResourcesSpec.from_dict(data)

                return resources_type_1
            except:  # noqa: E722
                pass
            return cast(Union["ResourcesSpec", None, Unset], data)

        resources = _parse_resources(d.pop("resources", UNSET))

        resources = cls(
            resources=resources,
        )

        resources.additional_properties = d
        return resources

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
