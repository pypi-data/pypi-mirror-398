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
    from ..models.assays_run_interactive_baseline_body_baseline_type_0_calculated_type_2_sliding_window import (
        AssaysRunInteractiveBaselineBodyBaselineType0CalculatedType2SlidingWindow,
    )


T = TypeVar("T", bound="AssaysRunInteractiveBaselineBodyBaselineType0CalculatedType2")


@_attrs_define
class AssaysRunInteractiveBaselineBodyBaselineType0CalculatedType2:
    """
    Attributes:
        sliding_window (AssaysRunInteractiveBaselineBodyBaselineType0CalculatedType2SlidingWindow):
    """

    sliding_window: (
        "AssaysRunInteractiveBaselineBodyBaselineType0CalculatedType2SlidingWindow"
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        sliding_window = self.sliding_window.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sliding_window": sliding_window,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assays_run_interactive_baseline_body_baseline_type_0_calculated_type_2_sliding_window import (
            AssaysRunInteractiveBaselineBodyBaselineType0CalculatedType2SlidingWindow,
        )

        d = dict(src_dict)
        sliding_window = AssaysRunInteractiveBaselineBodyBaselineType0CalculatedType2SlidingWindow.from_dict(
            d.pop("sliding_window")
        )

        assays_run_interactive_baseline_body_baseline_type_0_calculated_type_2 = cls(
            sliding_window=sliding_window,
        )

        assays_run_interactive_baseline_body_baseline_type_0_calculated_type_2.additional_properties = d
        return assays_run_interactive_baseline_body_baseline_type_0_calculated_type_2

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
