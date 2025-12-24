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
    from ..models.window_width_duration import WindowWidthDuration


T = TypeVar("T", bound="RollingWindow")


@_attrs_define
class RollingWindow:
    """[RollingWindow] can only be specified for background jobs and not individual /score calls.
    Describes the timeframe on InferenceResults to aggregate and compare against the Baseline.

        Attributes:
            width (WindowWidthDuration):
    """

    width: "WindowWidthDuration"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        width = self.width.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "width": width,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.window_width_duration import WindowWidthDuration

        d = dict(src_dict)
        width = WindowWidthDuration.from_dict(d.pop("width"))

        rolling_window = cls(
            width=width,
        )

        rolling_window.additional_properties = d
        return rolling_window

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
