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
    from ..models.baseline_type_0 import BaselineType0
    from ..models.baseline_type_1 import BaselineType1
    from ..models.baseline_type_2 import BaselineType2
    from ..models.baseline_type_3 import BaselineType3
    from ..models.summarizer_type_0 import SummarizerType0
    from ..models.summarizer_type_1 import SummarizerType1
    from ..models.targeting import Targeting


T = TypeVar("T", bound="RunBaselineRequest")


@_attrs_define
class RunBaselineRequest:
    """
    Attributes:
        baseline (Union['BaselineType0', 'BaselineType1', 'BaselineType2', 'BaselineType3']): The types of Baselines
            allowed
        summarizer (Union['SummarizerType0', 'SummarizerType1']): A [`Summarizer`] must implement [`Summarize`].
        targeting (Union['Targeting', None, Unset]):
    """

    baseline: Union["BaselineType0", "BaselineType1", "BaselineType2", "BaselineType3"]
    summarizer: Union["SummarizerType0", "SummarizerType1"]
    targeting: Union["Targeting", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.baseline_type_0 import BaselineType0
        from ..models.baseline_type_1 import BaselineType1
        from ..models.baseline_type_2 import BaselineType2
        from ..models.summarizer_type_0 import SummarizerType0
        from ..models.targeting import Targeting

        baseline: dict[str, Any]
        if isinstance(self.baseline, BaselineType0):
            baseline = self.baseline.to_dict()
        elif isinstance(self.baseline, BaselineType1):
            baseline = self.baseline.to_dict()
        elif isinstance(self.baseline, BaselineType2):
            baseline = self.baseline.to_dict()
        else:
            baseline = self.baseline.to_dict()

        summarizer: dict[str, Any]
        if isinstance(self.summarizer, SummarizerType0):
            summarizer = self.summarizer.to_dict()
        else:
            summarizer = self.summarizer.to_dict()

        targeting: Union[None, Unset, dict[str, Any]]
        if isinstance(self.targeting, Unset):
            targeting = UNSET
        elif isinstance(self.targeting, Targeting):
            targeting = self.targeting.to_dict()
        else:
            targeting = self.targeting

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "baseline": baseline,
                "summarizer": summarizer,
            }
        )
        if targeting is not UNSET:
            field_dict["targeting"] = targeting

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.baseline_type_0 import BaselineType0
        from ..models.baseline_type_1 import BaselineType1
        from ..models.baseline_type_2 import BaselineType2
        from ..models.baseline_type_3 import BaselineType3
        from ..models.summarizer_type_0 import SummarizerType0
        from ..models.summarizer_type_1 import SummarizerType1
        from ..models.targeting import Targeting

        d = dict(src_dict)

        def _parse_baseline(
            data: object,
        ) -> Union["BaselineType0", "BaselineType1", "BaselineType2", "BaselineType3"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_baseline_type_0 = BaselineType0.from_dict(data)

                return componentsschemas_baseline_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_baseline_type_1 = BaselineType1.from_dict(data)

                return componentsschemas_baseline_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_baseline_type_2 = BaselineType2.from_dict(data)

                return componentsschemas_baseline_type_2
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_baseline_type_3 = BaselineType3.from_dict(data)

            return componentsschemas_baseline_type_3

        baseline = _parse_baseline(d.pop("baseline"))

        def _parse_summarizer(
            data: object,
        ) -> Union["SummarizerType0", "SummarizerType1"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_summarizer_type_0 = SummarizerType0.from_dict(data)

                return componentsschemas_summarizer_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_summarizer_type_1 = SummarizerType1.from_dict(data)

            return componentsschemas_summarizer_type_1

        summarizer = _parse_summarizer(d.pop("summarizer"))

        def _parse_targeting(data: object) -> Union["Targeting", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                targeting_type_1 = Targeting.from_dict(data)

                return targeting_type_1
            except:  # noqa: E722
                pass
            return cast(Union["Targeting", None, Unset], data)

        targeting = _parse_targeting(d.pop("targeting", UNSET))

        run_baseline_request = cls(
            baseline=baseline,
            summarizer=summarizer,
            targeting=targeting,
        )

        run_baseline_request.additional_properties = d
        return run_baseline_request

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
