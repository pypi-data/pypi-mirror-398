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
    from ..models.assays_filter_response_200_item_baseline_type_0_calculated_type_2_sliding_window_window import (
        AssaysFilterResponse200ItemBaselineType0CalculatedType2SlidingWindowWindow,
    )


T = TypeVar(
    "T", bound="AssaysFilterResponse200ItemBaselineType0CalculatedType2SlidingWindow"
)


@_attrs_define
class AssaysFilterResponse200ItemBaselineType0CalculatedType2SlidingWindow:
    """
    Attributes:
        window (AssaysFilterResponse200ItemBaselineType0CalculatedType2SlidingWindowWindow):  Assay window.
        offset (str):
    """

    window: "AssaysFilterResponse200ItemBaselineType0CalculatedType2SlidingWindowWindow"
    offset: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        window = self.window.to_dict()

        offset = self.offset

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "window": window,
                "offset": offset,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assays_filter_response_200_item_baseline_type_0_calculated_type_2_sliding_window_window import (
            AssaysFilterResponse200ItemBaselineType0CalculatedType2SlidingWindowWindow,
        )

        d = dict(src_dict)
        window = AssaysFilterResponse200ItemBaselineType0CalculatedType2SlidingWindowWindow.from_dict(
            d.pop("window")
        )

        offset = d.pop("offset")

        assays_filter_response_200_item_baseline_type_0_calculated_type_2_sliding_window = cls(
            window=window,
            offset=offset,
        )

        assays_filter_response_200_item_baseline_type_0_calculated_type_2_sliding_window.additional_properties = d
        return assays_filter_response_200_item_baseline_type_0_calculated_type_2_sliding_window

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
