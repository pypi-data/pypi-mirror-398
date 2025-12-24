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
    from ..models.pg_interval import PGInterval


T = TypeVar("T", bound="RunFrequencyType1")


@_attrs_define
class RunFrequencyType1:
    """
    Attributes:
        simple_run_frequency (PGInterval): A struct that allows you to specify "Run every 3 days", where days is the
            `interval` [IntervalUnit] and 3 is the `skip`.
            This is used by Postgres (via init_assay_result.rs) to compute the next Start Time.
    """

    simple_run_frequency: "PGInterval"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        simple_run_frequency = self.simple_run_frequency.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "SimpleRunFrequency": simple_run_frequency,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pg_interval import PGInterval

        d = dict(src_dict)
        simple_run_frequency = PGInterval.from_dict(d.pop("SimpleRunFrequency"))

        run_frequency_type_1 = cls(
            simple_run_frequency=simple_run_frequency,
        )

        run_frequency_type_1.additional_properties = d
        return run_frequency_type_1

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
