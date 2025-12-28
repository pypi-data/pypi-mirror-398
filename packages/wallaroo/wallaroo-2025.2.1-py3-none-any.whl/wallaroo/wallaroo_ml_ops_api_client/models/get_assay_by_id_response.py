import datetime
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
)
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.baseline_type_0 import BaselineType0
    from ..models.baseline_type_1 import BaselineType1
    from ..models.baseline_type_2 import BaselineType2
    from ..models.baseline_type_3 import BaselineType3
    from ..models.rolling_window import RollingWindow
    from ..models.scheduling import Scheduling
    from ..models.summarizer_type_0 import SummarizerType0
    from ..models.summarizer_type_1 import SummarizerType1
    from ..models.targeting import Targeting


T = TypeVar("T", bound="GetAssayByIdResponse")


@_attrs_define
class GetAssayByIdResponse:
    """This represents an entry in the `assays_v2` table in the database.

    Attributes:
        baseline (Union['BaselineType0', 'BaselineType1', 'BaselineType2', 'BaselineType3']): The types of Baselines
            allowed
        scheduling (Scheduling): Controls how an assay is scheduled.
            We should be able to specify the start, end, and frequency.
        summarizer (Union['SummarizerType0', 'SummarizerType1']): A [`Summarizer`] must implement [`Summarize`].
        targeting (Targeting): Simple univariate assays only observe changes in one value in an InferenceResult.
            [`Targeting`] is our way of selecting what this value is.
        window (RollingWindow): [RollingWindow] can only be specified for background jobs and not individual /score
            calls.
            Describes the timeframe on InferenceResults to aggregate and compare against the Baseline.
        active (bool):
        created_at (datetime.datetime):
        id (UUID): The ID of the created AssayConfigV2
        name (str): A descriptive name displayed to the user for this Assay
        updated_at (datetime.datetime):
    """

    baseline: Union["BaselineType0", "BaselineType1", "BaselineType2", "BaselineType3"]
    scheduling: "Scheduling"
    summarizer: Union["SummarizerType0", "SummarizerType1"]
    targeting: "Targeting"
    window: "RollingWindow"
    active: bool
    created_at: datetime.datetime
    id: UUID
    name: str
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.baseline_type_0 import BaselineType0
        from ..models.baseline_type_1 import BaselineType1
        from ..models.baseline_type_2 import BaselineType2
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

        scheduling = self.scheduling.to_dict()

        summarizer: dict[str, Any]
        if isinstance(self.summarizer, SummarizerType0):
            summarizer = self.summarizer.to_dict()
        else:
            summarizer = self.summarizer.to_dict()

        targeting = self.targeting.to_dict()

        window = self.window.to_dict()

        active = self.active

        created_at = self.created_at.isoformat()

        id = str(self.id)

        name = self.name

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "baseline": baseline,
                "scheduling": scheduling,
                "summarizer": summarizer,
                "targeting": targeting,
                "window": window,
                "active": active,
                "created_at": created_at,
                "id": id,
                "name": name,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.baseline_type_0 import BaselineType0
        from ..models.baseline_type_1 import BaselineType1
        from ..models.baseline_type_2 import BaselineType2
        from ..models.baseline_type_3 import BaselineType3
        from ..models.rolling_window import RollingWindow
        from ..models.scheduling import Scheduling
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

        scheduling = Scheduling.from_dict(d.pop("scheduling"))

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

        window = RollingWindow.from_dict(d.pop("window"))

        active = d.pop("active")

        created_at = isoparse(d.pop("created_at"))

        id = UUID(d.pop("id"))

        name = d.pop("name")

        updated_at = isoparse(d.pop("updated_at"))

        get_assay_by_id_response = cls(
            baseline=baseline,
            scheduling=scheduling,
            summarizer=summarizer,
            targeting=targeting,
            window=window,
            active=active,
            created_at=created_at,
            id=id,
            name=name,
            updated_at=updated_at,
        )

        get_assay_by_id_response.additional_properties = d
        return get_assay_by_id_response

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
