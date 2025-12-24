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
    from ..models.list_all_orchestrations_response_item import (
        ListAllOrchestrationsResponseItem,
    )


T = TypeVar("T", bound="ListAllOrchestrationsResponse")


@_attrs_define
class ListAllOrchestrationsResponse:
    """
    Attributes:
        orchestrations (list['ListAllOrchestrationsResponseItem']):
    """

    orchestrations: list["ListAllOrchestrationsResponseItem"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        orchestrations = []
        for orchestrations_item_data in self.orchestrations:
            orchestrations_item = orchestrations_item_data.to_dict()
            orchestrations.append(orchestrations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "orchestrations": orchestrations,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.list_all_orchestrations_response_item import (
            ListAllOrchestrationsResponseItem,
        )

        d = dict(src_dict)
        orchestrations = []
        _orchestrations = d.pop("orchestrations")
        for orchestrations_item_data in _orchestrations:
            orchestrations_item = ListAllOrchestrationsResponseItem.from_dict(
                orchestrations_item_data
            )

            orchestrations.append(orchestrations_item)

        list_all_orchestrations_response = cls(
            orchestrations=orchestrations,
        )

        list_all_orchestrations_response.additional_properties = d
        return list_all_orchestrations_response

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
