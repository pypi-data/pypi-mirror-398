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
    from ..models.baseline_type_0 import BaselineType0
    from ..models.baseline_type_1 import BaselineType1
    from ..models.baseline_type_2 import BaselineType2
    from ..models.baseline_type_3 import BaselineType3
    from ..models.raw import Raw
    from ..models.stored import Stored
    from ..models.summarizer_type_0 import SummarizerType0
    from ..models.summarizer_type_1 import SummarizerType1
    from ..models.targeting import Targeting


T = TypeVar("T", bound="ScoreRequest")


@_attrs_define
class ScoreRequest:
    """
    Attributes:
        baseline (Union['BaselineType0', 'BaselineType1', 'BaselineType2', 'BaselineType3']): The types of Baselines
            allowed
        summarizer (Union['SummarizerType0', 'SummarizerType1']): A [`Summarizer`] must implement [`Summarize`].
        targeting (Targeting): Simple univariate assays only observe changes in one value in an InferenceResult.
            [`Targeting`] is our way of selecting what this value is.
        window (Union['Raw', 'Stored']): This is only used for calls to the /score endpoint and not for background jobs.
            Describes the timeframe on InferenceResults to aggregate and compare against the Baseline.
    """

    baseline: Union["BaselineType0", "BaselineType1", "BaselineType2", "BaselineType3"]
    summarizer: Union["SummarizerType0", "SummarizerType1"]
    targeting: "Targeting"
    window: Union["Raw", "Stored"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.baseline_type_0 import BaselineType0
        from ..models.baseline_type_1 import BaselineType1
        from ..models.baseline_type_2 import BaselineType2
        from ..models.raw import Raw
        from ..models.summarizer_type_0 import SummarizerType0

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

        targeting = self.targeting.to_dict()

        window: dict[str, Any]
        if isinstance(self.window, Raw):
            window = self.window.to_dict()
        else:
            window = self.window.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "baseline": baseline,
                "summarizer": summarizer,
                "targeting": targeting,
                "window": window,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.baseline_type_0 import BaselineType0
        from ..models.baseline_type_1 import BaselineType1
        from ..models.baseline_type_2 import BaselineType2
        from ..models.baseline_type_3 import BaselineType3
        from ..models.raw import Raw
        from ..models.stored import Stored
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

        targeting = Targeting.from_dict(d.pop("targeting"))

        def _parse_window(data: object) -> Union["Raw", "Stored"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_static_window_raw = Raw.from_dict(data)

                return componentsschemas_static_window_raw
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_static_window_stored = Stored.from_dict(data)

            return componentsschemas_static_window_stored

        window = _parse_window(d.pop("window"))

        score_request = cls(
            baseline=baseline,
            summarizer=summarizer,
            targeting=targeting,
            window=window,
        )

        score_request.additional_properties = d
        return score_request

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
