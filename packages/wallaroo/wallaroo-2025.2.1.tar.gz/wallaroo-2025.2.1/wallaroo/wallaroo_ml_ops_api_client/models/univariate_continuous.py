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

from ..models.aggregation import Aggregation
from ..models.bin_mode_type_0 import BinModeType0
from ..models.metric import Metric
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bin_mode_type_1 import BinModeType1
    from ..models.bin_mode_type_2 import BinModeType2
    from ..models.bin_mode_type_3 import BinModeType3
    from ..models.bin_mode_type_4 import BinModeType4


T = TypeVar("T", bound="UnivariateContinuous")


@_attrs_define
class UnivariateContinuous:
    """Defines the summarizer/test we want to conduct

    Attributes:
        aggregation (Aggregation):
        bin_mode (Union['BinModeType1', 'BinModeType2', 'BinModeType3', 'BinModeType4', BinModeType0]):
        metric (Metric): How we calculate the score between two histograms/vecs.
        bin_weights (Union[None, Unset, list[float]]): Weights to bias the scoring function. Can be used to focus on
            tails or specific bins.
    """

    aggregation: Aggregation
    bin_mode: Union[
        "BinModeType1", "BinModeType2", "BinModeType3", "BinModeType4", BinModeType0
    ]
    metric: Metric
    bin_weights: Union[None, Unset, list[float]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.bin_mode_type_1 import BinModeType1
        from ..models.bin_mode_type_2 import BinModeType2
        from ..models.bin_mode_type_3 import BinModeType3

        aggregation = self.aggregation.value

        bin_mode: Union[dict[str, Any], str]
        if isinstance(self.bin_mode, BinModeType0):
            bin_mode = self.bin_mode.value
        elif isinstance(self.bin_mode, BinModeType1):
            bin_mode = self.bin_mode.to_dict()
        elif isinstance(self.bin_mode, BinModeType2):
            bin_mode = self.bin_mode.to_dict()
        elif isinstance(self.bin_mode, BinModeType3):
            bin_mode = self.bin_mode.to_dict()
        else:
            bin_mode = self.bin_mode.to_dict()

        metric = self.metric.value

        bin_weights: Union[None, Unset, list[float]]
        if isinstance(self.bin_weights, Unset):
            bin_weights = UNSET
        elif isinstance(self.bin_weights, list):
            bin_weights = self.bin_weights

        else:
            bin_weights = self.bin_weights

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "aggregation": aggregation,
                "bin_mode": bin_mode,
                "metric": metric,
            }
        )
        if bin_weights is not UNSET:
            field_dict["bin_weights"] = bin_weights

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.bin_mode_type_1 import BinModeType1
        from ..models.bin_mode_type_2 import BinModeType2
        from ..models.bin_mode_type_3 import BinModeType3
        from ..models.bin_mode_type_4 import BinModeType4

        d = dict(src_dict)
        aggregation = Aggregation(d.pop("aggregation"))

        def _parse_bin_mode(
            data: object,
        ) -> Union[
            "BinModeType1", "BinModeType2", "BinModeType3", "BinModeType4", BinModeType0
        ]:
            try:
                if not isinstance(data, str):
                    raise TypeError()
                componentsschemas_bin_mode_type_0 = BinModeType0(data)

                return componentsschemas_bin_mode_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_bin_mode_type_1 = BinModeType1.from_dict(data)

                return componentsschemas_bin_mode_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_bin_mode_type_2 = BinModeType2.from_dict(data)

                return componentsschemas_bin_mode_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_bin_mode_type_3 = BinModeType3.from_dict(data)

                return componentsschemas_bin_mode_type_3
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_bin_mode_type_4 = BinModeType4.from_dict(data)

            return componentsschemas_bin_mode_type_4

        bin_mode = _parse_bin_mode(d.pop("bin_mode"))

        metric = Metric(d.pop("metric"))

        def _parse_bin_weights(data: object) -> Union[None, Unset, list[float]]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                bin_weights_type_0 = cast(list[float], data)

                return bin_weights_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, list[float]], data)

        bin_weights = _parse_bin_weights(d.pop("bin_weights", UNSET))

        univariate_continuous = cls(
            aggregation=aggregation,
            bin_mode=bin_mode,
            metric=metric,
            bin_weights=bin_weights,
        )

        univariate_continuous.additional_properties = d
        return univariate_continuous

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
