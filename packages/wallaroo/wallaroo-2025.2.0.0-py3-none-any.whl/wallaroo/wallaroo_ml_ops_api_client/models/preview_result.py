import datetime
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.preview_result_summaries import PreviewResultSummaries
    from ..models.scores import Scores


T = TypeVar("T", bound="PreviewResult")


@_attrs_define
class PreviewResult:
    """
    Attributes:
        analyzed_at (datetime.datetime):
        assay_id (UUID):
        elapsed_millis (int):
        id (int):
        pipeline_id (int):
        scores (Scores):
        summaries (PreviewResultSummaries):
        window_end (datetime.datetime):
        workspace_id (int):
        workspace_name (str):
    """

    analyzed_at: datetime.datetime
    assay_id: UUID
    elapsed_millis: int
    id: int
    pipeline_id: int
    scores: "Scores"
    summaries: "PreviewResultSummaries"
    window_end: datetime.datetime
    workspace_id: int
    workspace_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        analyzed_at = self.analyzed_at.isoformat()

        assay_id = str(self.assay_id)

        elapsed_millis = self.elapsed_millis

        id = self.id

        pipeline_id = self.pipeline_id

        scores = self.scores.to_dict()

        summaries = self.summaries.to_dict()

        window_end = self.window_end.isoformat()

        workspace_id = self.workspace_id

        workspace_name = self.workspace_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "analyzed_at": analyzed_at,
                "assay_id": assay_id,
                "elapsed_millis": elapsed_millis,
                "id": id,
                "pipeline_id": pipeline_id,
                "scores": scores,
                "summaries": summaries,
                "window_end": window_end,
                "workspace_id": workspace_id,
                "workspace_name": workspace_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.preview_result_summaries import PreviewResultSummaries
        from ..models.scores import Scores

        d = dict(src_dict)
        analyzed_at = isoparse(d.pop("analyzed_at"))

        assay_id = UUID(d.pop("assay_id"))

        elapsed_millis = d.pop("elapsed_millis")

        id = d.pop("id")

        pipeline_id = d.pop("pipeline_id")

        scores = Scores.from_dict(d.pop("scores"))

        summaries = PreviewResultSummaries.from_dict(d.pop("summaries"))

        window_end = isoparse(d.pop("window_end"))

        workspace_id = d.pop("workspace_id")

        workspace_name = d.pop("workspace_name")

        preview_result = cls(
            analyzed_at=analyzed_at,
            assay_id=assay_id,
            elapsed_millis=elapsed_millis,
            id=id,
            pipeline_id=pipeline_id,
            scores=scores,
            summaries=summaries,
            window_end=window_end,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
        )

        preview_result.additional_properties = d
        return preview_result

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
