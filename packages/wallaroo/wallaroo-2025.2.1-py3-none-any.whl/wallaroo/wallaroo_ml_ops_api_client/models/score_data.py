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

T = TypeVar("T", bound="ScoreData")


@_attrs_define
class ScoreData:
    """
    Attributes:
        score (float): The score for a given window and baseline summary.
        scores (list[float]): The score differences for each bin.
        bin_index (Union[None, Unset, int]): The index of the bin where the maximum score difference occurs when MaxDiff
            metric is used.
    """

    score: float
    scores: list[float]
    bin_index: Union[None, Unset, int] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        score = self.score

        scores = self.scores

        bin_index: Union[None, Unset, int]
        if isinstance(self.bin_index, Unset):
            bin_index = UNSET
        else:
            bin_index = self.bin_index

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "score": score,
                "scores": scores,
            }
        )
        if bin_index is not UNSET:
            field_dict["bin_index"] = bin_index

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        score = d.pop("score")

        scores = cast(list[float], d.pop("scores"))

        def _parse_bin_index(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bin_index = _parse_bin_index(d.pop("bin_index", UNSET))

        score_data = cls(
            score=score,
            scores=scores,
            bin_index=bin_index,
        )

        score_data.additional_properties = d
        return score_data

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
