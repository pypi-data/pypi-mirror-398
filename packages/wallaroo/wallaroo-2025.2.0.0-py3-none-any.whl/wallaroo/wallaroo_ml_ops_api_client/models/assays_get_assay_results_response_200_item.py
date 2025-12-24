import datetime
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
from dateutil.parser import isoparse

from ..models.assays_get_assay_results_response_200_item_status import (
    AssaysGetAssayResultsResponse200ItemStatus,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.assays_get_assay_results_response_200_item_baseline_summary import (
        AssaysGetAssayResultsResponse200ItemBaselineSummary,
    )
    from ..models.assays_get_assay_results_response_200_item_summarizer_type_0 import (
        AssaysGetAssayResultsResponse200ItemSummarizerType0,
    )
    from ..models.assays_get_assay_results_response_200_item_summarizer_type_1 import (
        AssaysGetAssayResultsResponse200ItemSummarizerType1,
    )
    from ..models.assays_get_assay_results_response_200_item_window_summary import (
        AssaysGetAssayResultsResponse200ItemWindowSummary,
    )


T = TypeVar("T", bound="AssaysGetAssayResultsResponse200Item")


@_attrs_define
class AssaysGetAssayResultsResponse200Item:
    """
    Attributes:
        window_start (datetime.datetime):
        analyzed_at (datetime.datetime):
        elapsed_millis (int):
        baseline_summary (AssaysGetAssayResultsResponse200ItemBaselineSummary):  Result from summarizing one sample
            collection.
        window_summary (AssaysGetAssayResultsResponse200ItemWindowSummary):  Result from summarizing one sample
            collection.
        alert_threshold (float):
        score (float):
        scores (list[float]):
        summarizer (Union['AssaysGetAssayResultsResponse200ItemSummarizerType0',
            'AssaysGetAssayResultsResponse200ItemSummarizerType1']):
        status (AssaysGetAssayResultsResponse200ItemStatus):
        id (Union[None, Unset, int]):
        assay_id (Union[None, Unset, int]):
        pipeline_id (Union[None, Unset, int]):
        workspace_id (Union[None, Unset, int]):
        workspace_name (Union[None, Unset, str]):
        warning_threshold (Union[None, Unset, float]):
        bin_index (Union[None, Unset, int]):
        created_at (Union[None, Unset, datetime.datetime]):
    """

    window_start: datetime.datetime
    analyzed_at: datetime.datetime
    elapsed_millis: int
    baseline_summary: "AssaysGetAssayResultsResponse200ItemBaselineSummary"
    window_summary: "AssaysGetAssayResultsResponse200ItemWindowSummary"
    alert_threshold: float
    score: float
    scores: list[float]
    summarizer: Union[
        "AssaysGetAssayResultsResponse200ItemSummarizerType0",
        "AssaysGetAssayResultsResponse200ItemSummarizerType1",
    ]
    status: AssaysGetAssayResultsResponse200ItemStatus
    id: Union[None, Unset, int] = UNSET
    assay_id: Union[None, Unset, int] = UNSET
    pipeline_id: Union[None, Unset, int] = UNSET
    workspace_id: Union[None, Unset, int] = UNSET
    workspace_name: Union[None, Unset, str] = UNSET
    warning_threshold: Union[None, Unset, float] = UNSET
    bin_index: Union[None, Unset, int] = UNSET
    created_at: Union[None, Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.assays_get_assay_results_response_200_item_summarizer_type_0 import (
            AssaysGetAssayResultsResponse200ItemSummarizerType0,
        )

        window_start = self.window_start.isoformat()

        analyzed_at = self.analyzed_at.isoformat()

        elapsed_millis = self.elapsed_millis

        baseline_summary = self.baseline_summary.to_dict()

        window_summary = self.window_summary.to_dict()

        alert_threshold = self.alert_threshold

        score = self.score

        scores = self.scores

        summarizer: dict[str, Any]
        if isinstance(
            self.summarizer, AssaysGetAssayResultsResponse200ItemSummarizerType0
        ):
            summarizer = self.summarizer.to_dict()
        else:
            summarizer = self.summarizer.to_dict()

        status = self.status.value

        id: Union[None, Unset, int]
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        assay_id: Union[None, Unset, int]
        if isinstance(self.assay_id, Unset):
            assay_id = UNSET
        else:
            assay_id = self.assay_id

        pipeline_id: Union[None, Unset, int]
        if isinstance(self.pipeline_id, Unset):
            pipeline_id = UNSET
        else:
            pipeline_id = self.pipeline_id

        workspace_id: Union[None, Unset, int]
        if isinstance(self.workspace_id, Unset):
            workspace_id = UNSET
        else:
            workspace_id = self.workspace_id

        workspace_name: Union[None, Unset, str]
        if isinstance(self.workspace_name, Unset):
            workspace_name = UNSET
        else:
            workspace_name = self.workspace_name

        warning_threshold: Union[None, Unset, float]
        if isinstance(self.warning_threshold, Unset):
            warning_threshold = UNSET
        else:
            warning_threshold = self.warning_threshold

        bin_index: Union[None, Unset, int]
        if isinstance(self.bin_index, Unset):
            bin_index = UNSET
        else:
            bin_index = self.bin_index

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        elif isinstance(self.created_at, datetime.datetime):
            created_at = self.created_at.isoformat()
        else:
            created_at = self.created_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "window_start": window_start,
                "analyzed_at": analyzed_at,
                "elapsed_millis": elapsed_millis,
                "baseline_summary": baseline_summary,
                "window_summary": window_summary,
                "alert_threshold": alert_threshold,
                "score": score,
                "scores": scores,
                "summarizer": summarizer,
                "status": status,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if assay_id is not UNSET:
            field_dict["assay_id"] = assay_id
        if pipeline_id is not UNSET:
            field_dict["pipeline_id"] = pipeline_id
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id
        if workspace_name is not UNSET:
            field_dict["workspace_name"] = workspace_name
        if warning_threshold is not UNSET:
            field_dict["warning_threshold"] = warning_threshold
        if bin_index is not UNSET:
            field_dict["bin_index"] = bin_index
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assays_get_assay_results_response_200_item_baseline_summary import (
            AssaysGetAssayResultsResponse200ItemBaselineSummary,
        )
        from ..models.assays_get_assay_results_response_200_item_summarizer_type_0 import (
            AssaysGetAssayResultsResponse200ItemSummarizerType0,
        )
        from ..models.assays_get_assay_results_response_200_item_summarizer_type_1 import (
            AssaysGetAssayResultsResponse200ItemSummarizerType1,
        )
        from ..models.assays_get_assay_results_response_200_item_window_summary import (
            AssaysGetAssayResultsResponse200ItemWindowSummary,
        )

        d = dict(src_dict)
        window_start = isoparse(d.pop("window_start"))

        analyzed_at = isoparse(d.pop("analyzed_at"))

        elapsed_millis = d.pop("elapsed_millis")

        baseline_summary = (
            AssaysGetAssayResultsResponse200ItemBaselineSummary.from_dict(
                d.pop("baseline_summary")
            )
        )

        window_summary = AssaysGetAssayResultsResponse200ItemWindowSummary.from_dict(
            d.pop("window_summary")
        )

        alert_threshold = d.pop("alert_threshold")

        score = d.pop("score")

        scores = cast(list[float], d.pop("scores"))

        def _parse_summarizer(
            data: object,
        ) -> Union[
            "AssaysGetAssayResultsResponse200ItemSummarizerType0",
            "AssaysGetAssayResultsResponse200ItemSummarizerType1",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                summarizer_type_0 = (
                    AssaysGetAssayResultsResponse200ItemSummarizerType0.from_dict(data)
                )

                return summarizer_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            summarizer_type_1 = (
                AssaysGetAssayResultsResponse200ItemSummarizerType1.from_dict(data)
            )

            return summarizer_type_1

        summarizer = _parse_summarizer(d.pop("summarizer"))

        status = AssaysGetAssayResultsResponse200ItemStatus(d.pop("status"))

        def _parse_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_assay_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        assay_id = _parse_assay_id(d.pop("assay_id", UNSET))

        def _parse_pipeline_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        pipeline_id = _parse_pipeline_id(d.pop("pipeline_id", UNSET))

        def _parse_workspace_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        workspace_id = _parse_workspace_id(d.pop("workspace_id", UNSET))

        def _parse_workspace_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        workspace_name = _parse_workspace_name(d.pop("workspace_name", UNSET))

        def _parse_warning_threshold(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        warning_threshold = _parse_warning_threshold(d.pop("warning_threshold", UNSET))

        def _parse_bin_index(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        bin_index = _parse_bin_index(d.pop("bin_index", UNSET))

        def _parse_created_at(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                created_at_type_0 = isoparse(data)

                return created_at_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        assays_get_assay_results_response_200_item = cls(
            window_start=window_start,
            analyzed_at=analyzed_at,
            elapsed_millis=elapsed_millis,
            baseline_summary=baseline_summary,
            window_summary=window_summary,
            alert_threshold=alert_threshold,
            score=score,
            scores=scores,
            summarizer=summarizer,
            status=status,
            id=id,
            assay_id=assay_id,
            pipeline_id=pipeline_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            warning_threshold=warning_threshold,
            bin_index=bin_index,
            created_at=created_at,
        )

        assays_get_assay_results_response_200_item.additional_properties = d
        return assays_get_assay_results_response_200_item

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
