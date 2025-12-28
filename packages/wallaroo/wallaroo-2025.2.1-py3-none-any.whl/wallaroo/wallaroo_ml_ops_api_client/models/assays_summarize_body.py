from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.assays_summarize_body_baseline_type_0 import (
        AssaysSummarizeBodyBaselineType0,
    )
    from ..models.assays_summarize_body_baseline_type_1 import (
        AssaysSummarizeBodyBaselineType1,
    )
    from ..models.assays_summarize_body_baseline_type_2 import (
        AssaysSummarizeBodyBaselineType2,
    )
    from ..models.assays_summarize_body_summarizer_type_0 import (
        AssaysSummarizeBodySummarizerType0,
    )
    from ..models.assays_summarize_body_summarizer_type_1 import (
        AssaysSummarizeBodySummarizerType1,
    )


T = TypeVar("T", bound="AssaysSummarizeBody")


@_attrs_define
class AssaysSummarizeBody:
    """
    Attributes:
        summarizer (Union['AssaysSummarizeBodySummarizerType0', 'AssaysSummarizeBodySummarizerType1']):
        baseline (Union['AssaysSummarizeBodyBaselineType0', 'AssaysSummarizeBodyBaselineType1',
            'AssaysSummarizeBodyBaselineType2']):
    """

    summarizer: Union[
        "AssaysSummarizeBodySummarizerType0", "AssaysSummarizeBodySummarizerType1"
    ]
    baseline: Union[
        "AssaysSummarizeBodyBaselineType0",
        "AssaysSummarizeBodyBaselineType1",
        "AssaysSummarizeBodyBaselineType2",
    ]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.assays_summarize_body_baseline_type_0 import (
            AssaysSummarizeBodyBaselineType0,
        )
        from ..models.assays_summarize_body_baseline_type_1 import (
            AssaysSummarizeBodyBaselineType1,
        )
        from ..models.assays_summarize_body_summarizer_type_0 import (
            AssaysSummarizeBodySummarizerType0,
        )

        summarizer: dict[str, Any]
        if isinstance(self.summarizer, AssaysSummarizeBodySummarizerType0):
            summarizer = self.summarizer.to_dict()
        else:
            summarizer = self.summarizer.to_dict()

        baseline: dict[str, Any]
        if isinstance(self.baseline, AssaysSummarizeBodyBaselineType0):
            baseline = self.baseline.to_dict()
        elif isinstance(self.baseline, AssaysSummarizeBodyBaselineType1):
            baseline = self.baseline.to_dict()
        else:
            baseline = self.baseline.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "summarizer": summarizer,
                "baseline": baseline,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assays_summarize_body_baseline_type_0 import (
            AssaysSummarizeBodyBaselineType0,
        )
        from ..models.assays_summarize_body_baseline_type_1 import (
            AssaysSummarizeBodyBaselineType1,
        )
        from ..models.assays_summarize_body_baseline_type_2 import (
            AssaysSummarizeBodyBaselineType2,
        )
        from ..models.assays_summarize_body_summarizer_type_0 import (
            AssaysSummarizeBodySummarizerType0,
        )
        from ..models.assays_summarize_body_summarizer_type_1 import (
            AssaysSummarizeBodySummarizerType1,
        )

        d = dict(src_dict)

        def _parse_summarizer(
            data: object,
        ) -> Union[
            "AssaysSummarizeBodySummarizerType0", "AssaysSummarizeBodySummarizerType1"
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                summarizer_type_0 = AssaysSummarizeBodySummarizerType0.from_dict(data)

                return summarizer_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            summarizer_type_1 = AssaysSummarizeBodySummarizerType1.from_dict(data)

            return summarizer_type_1

        summarizer = _parse_summarizer(d.pop("summarizer"))

        def _parse_baseline(
            data: object,
        ) -> Union[
            "AssaysSummarizeBodyBaselineType0",
            "AssaysSummarizeBodyBaselineType1",
            "AssaysSummarizeBodyBaselineType2",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                baseline_type_0 = AssaysSummarizeBodyBaselineType0.from_dict(data)

                return baseline_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                baseline_type_1 = AssaysSummarizeBodyBaselineType1.from_dict(data)

                return baseline_type_1
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            baseline_type_2 = AssaysSummarizeBodyBaselineType2.from_dict(data)

            return baseline_type_2

        baseline = _parse_baseline(d.pop("baseline"))

        assays_summarize_body = cls(
            summarizer=summarizer,
            baseline=baseline,
        )

        assays_summarize_body.additional_properties = d
        return assays_summarize_body

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
