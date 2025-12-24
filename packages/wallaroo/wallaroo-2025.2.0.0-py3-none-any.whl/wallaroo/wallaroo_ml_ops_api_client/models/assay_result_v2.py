import datetime
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.assay_status import AssayStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.field_tagged_summaries import FieldTaggedSummaries
    from ..models.scores import Scores


T = TypeVar("T", bound="AssayResultV2")


@_attrs_define
class AssayResultV2:
    """
    Attributes:
        analyzed_at (datetime.datetime): The time the assay was analyzed.
        assay_id (UUID): The ID of the assay.
        created_at (datetime.datetime): The time the assay result was created.
        elapsed_millis (int): The time the assay took to analyze.
        id (int): Auto-incrementing integer for assays v1 compatibility.
        pipeline_id (int): The pipeline ID this assay result is for.
        status (AssayStatus):
        updated_at (datetime.datetime): The time the assay result was updated.
        window_end (datetime.datetime):
        window_start (datetime.datetime):
        workspace_id (int): The workspace ID this assay result is for.
        workspace_name (str): The workspace name this assay result is for.
        alert_threshold (Union[None, Unset, float]): The alert threshold for this assay result.
        scores (Union['Scores', None, Unset]):
        summaries (Union['FieldTaggedSummaries', None, Unset]):
        warning_threshold (Union[None, Unset, float]): The warning threshold for this assay result.
    """

    analyzed_at: datetime.datetime
    assay_id: UUID
    created_at: datetime.datetime
    elapsed_millis: int
    id: int
    pipeline_id: int
    status: AssayStatus
    updated_at: datetime.datetime
    window_end: datetime.datetime
    window_start: datetime.datetime
    workspace_id: int
    workspace_name: str
    alert_threshold: Union[None, Unset, float] = UNSET
    scores: Union["Scores", None, Unset] = UNSET
    summaries: Union["FieldTaggedSummaries", None, Unset] = UNSET
    warning_threshold: Union[None, Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.field_tagged_summaries import FieldTaggedSummaries
        from ..models.scores import Scores

        analyzed_at = self.analyzed_at.isoformat()

        assay_id = str(self.assay_id)

        created_at = self.created_at.isoformat()

        elapsed_millis = self.elapsed_millis

        id = self.id

        pipeline_id = self.pipeline_id

        status = self.status.value

        updated_at = self.updated_at.isoformat()

        window_end = self.window_end.isoformat()

        window_start = self.window_start.isoformat()

        workspace_id = self.workspace_id

        workspace_name = self.workspace_name

        alert_threshold: Union[None, Unset, float]
        if isinstance(self.alert_threshold, Unset):
            alert_threshold = UNSET
        else:
            alert_threshold = self.alert_threshold

        scores: Union[None, Unset, dict[str, Any]]
        if isinstance(self.scores, Unset):
            scores = UNSET
        elif isinstance(self.scores, Scores):
            scores = self.scores.to_dict()
        else:
            scores = self.scores

        summaries: Union[None, Unset, dict[str, Any]]
        if isinstance(self.summaries, Unset):
            summaries = UNSET
        elif isinstance(self.summaries, FieldTaggedSummaries):
            summaries = self.summaries.to_dict()
        else:
            summaries = self.summaries

        warning_threshold: Union[None, Unset, float]
        if isinstance(self.warning_threshold, Unset):
            warning_threshold = UNSET
        else:
            warning_threshold = self.warning_threshold

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "analyzed_at": analyzed_at,
                "assay_id": assay_id,
                "created_at": created_at,
                "elapsed_millis": elapsed_millis,
                "id": id,
                "pipeline_id": pipeline_id,
                "status": status,
                "updated_at": updated_at,
                "window_end": window_end,
                "window_start": window_start,
                "workspace_id": workspace_id,
                "workspace_name": workspace_name,
            }
        )
        if alert_threshold is not UNSET:
            field_dict["alert_threshold"] = alert_threshold
        if scores is not UNSET:
            field_dict["scores"] = scores
        if summaries is not UNSET:
            field_dict["summaries"] = summaries
        if warning_threshold is not UNSET:
            field_dict["warning_threshold"] = warning_threshold

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.field_tagged_summaries import FieldTaggedSummaries
        from ..models.scores import Scores

        d = dict(src_dict)
        analyzed_at = isoparse(d.pop("analyzed_at"))

        assay_id = UUID(d.pop("assay_id"))

        created_at = isoparse(d.pop("created_at"))

        elapsed_millis = d.pop("elapsed_millis")

        id = d.pop("id")

        pipeline_id = d.pop("pipeline_id")

        status = AssayStatus(d.pop("status"))

        updated_at = isoparse(d.pop("updated_at"))

        window_end = isoparse(d.pop("window_end"))

        window_start = isoparse(d.pop("window_start"))

        workspace_id = d.pop("workspace_id")

        workspace_name = d.pop("workspace_name")

        def _parse_alert_threshold(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        alert_threshold = _parse_alert_threshold(d.pop("alert_threshold", UNSET))

        def _parse_scores(data: object) -> Union["Scores", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                scores_type_1 = Scores.from_dict(data)

                return scores_type_1
            except:  # noqa: E722
                pass
            return cast(Union["Scores", None, Unset], data)

        scores = _parse_scores(d.pop("scores", UNSET))

        def _parse_summaries(
            data: object,
        ) -> Union["FieldTaggedSummaries", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                summaries_type_1 = FieldTaggedSummaries.from_dict(data)

                return summaries_type_1
            except:  # noqa: E722
                pass
            return cast(Union["FieldTaggedSummaries", None, Unset], data)

        summaries = _parse_summaries(d.pop("summaries", UNSET))

        def _parse_warning_threshold(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        warning_threshold = _parse_warning_threshold(d.pop("warning_threshold", UNSET))

        assay_result_v2 = cls(
            analyzed_at=analyzed_at,
            assay_id=assay_id,
            created_at=created_at,
            elapsed_millis=elapsed_millis,
            id=id,
            pipeline_id=pipeline_id,
            status=status,
            updated_at=updated_at,
            window_end=window_end,
            window_start=window_start,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            alert_threshold=alert_threshold,
            scores=scores,
            summaries=summaries,
            warning_threshold=warning_threshold,
        )

        assay_result_v2.additional_properties = d
        return assay_result_v2

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
