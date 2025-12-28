from collections.abc import Mapping
from typing import (
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

T = TypeVar("T", bound="Thresholds")


@_attrs_define
class Thresholds:
    """Thresholds are user-configured values that can be used to indicate that the system should
    take additional action when scores deviate. The minimum action is to indicate these deviations
    on graphs with different colors.

        Attributes:
            alert (Union[None, Unset, float]):
            warning (Union[None, Unset, float]):
    """

    alert: Union[None, Unset, float] = UNSET
    warning: Union[None, Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        alert: Union[None, Unset, float]
        if isinstance(self.alert, Unset):
            alert = UNSET
        else:
            alert = self.alert

        warning: Union[None, Unset, float]
        if isinstance(self.warning, Unset):
            warning = UNSET
        else:
            warning = self.warning

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if alert is not UNSET:
            field_dict["alert"] = alert
        if warning is not UNSET:
            field_dict["warning"] = warning

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_alert(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        alert = _parse_alert(d.pop("alert", UNSET))

        def _parse_warning(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        warning = _parse_warning(d.pop("warning", UNSET))

        thresholds = cls(
            alert=alert,
            warning=warning,
        )

        thresholds.additional_properties = d
        return thresholds

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
