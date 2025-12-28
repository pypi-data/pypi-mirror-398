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

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.assays_run_interactive_baseline_body_baseline_type_0 import (
        AssaysRunInteractiveBaselineBodyBaselineType0,
    )
    from ..models.assays_run_interactive_baseline_body_baseline_type_1 import (
        AssaysRunInteractiveBaselineBodyBaselineType1,
    )
    from ..models.assays_run_interactive_baseline_body_summarizer_type_0 import (
        AssaysRunInteractiveBaselineBodySummarizerType0,
    )
    from ..models.assays_run_interactive_baseline_body_summarizer_type_1 import (
        AssaysRunInteractiveBaselineBodySummarizerType1,
    )
    from ..models.assays_run_interactive_baseline_body_window import (
        AssaysRunInteractiveBaselineBodyWindow,
    )


T = TypeVar("T", bound="AssaysRunInteractiveBaselineBody")


@_attrs_define
class AssaysRunInteractiveBaselineBody:
    """Request for interactive assay baseline.

    Attributes:
        name (str):
        pipeline_id (int):
        pipeline_name (str):
        active (bool):
        status (str):
        baseline (Union['AssaysRunInteractiveBaselineBodyBaselineType0',
            'AssaysRunInteractiveBaselineBodyBaselineType1']):
        window (AssaysRunInteractiveBaselineBodyWindow):  Assay window.
        summarizer (Union['AssaysRunInteractiveBaselineBodySummarizerType0',
            'AssaysRunInteractiveBaselineBodySummarizerType1']):
        alert_threshold (float):
        created_at (datetime.datetime):
        workspace_id (int):
        id (Union[None, Unset, int]):
        warning_threshold (Union[None, Unset, float]):
        last_window_start (Union[None, Unset, datetime.datetime]):
        run_until (Union[None, Unset, datetime.datetime]):
        last_run (Union[None, Unset, datetime.datetime]):
    """

    name: str
    pipeline_id: int
    pipeline_name: str
    active: bool
    status: str
    baseline: Union[
        "AssaysRunInteractiveBaselineBodyBaselineType0",
        "AssaysRunInteractiveBaselineBodyBaselineType1",
    ]
    window: "AssaysRunInteractiveBaselineBodyWindow"
    summarizer: Union[
        "AssaysRunInteractiveBaselineBodySummarizerType0",
        "AssaysRunInteractiveBaselineBodySummarizerType1",
    ]
    alert_threshold: float
    created_at: datetime.datetime
    workspace_id: int
    id: Union[None, Unset, int] = UNSET
    warning_threshold: Union[None, Unset, float] = UNSET
    last_window_start: Union[None, Unset, datetime.datetime] = UNSET
    run_until: Union[None, Unset, datetime.datetime] = UNSET
    last_run: Union[None, Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.assays_run_interactive_baseline_body_baseline_type_0 import (
            AssaysRunInteractiveBaselineBodyBaselineType0,
        )
        from ..models.assays_run_interactive_baseline_body_summarizer_type_0 import (
            AssaysRunInteractiveBaselineBodySummarizerType0,
        )

        name = self.name

        pipeline_id = self.pipeline_id

        pipeline_name = self.pipeline_name

        active = self.active

        status = self.status

        baseline: dict[str, Any]
        if isinstance(self.baseline, AssaysRunInteractiveBaselineBodyBaselineType0):
            baseline = self.baseline.to_dict()
        else:
            baseline = self.baseline.to_dict()

        window = self.window.to_dict()

        summarizer: dict[str, Any]
        if isinstance(self.summarizer, AssaysRunInteractiveBaselineBodySummarizerType0):
            summarizer = self.summarizer.to_dict()
        else:
            summarizer = self.summarizer.to_dict()

        alert_threshold = self.alert_threshold

        created_at = self.created_at.isoformat()

        workspace_id = self.workspace_id

        id: Union[None, Unset, int]
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        warning_threshold: Union[None, Unset, float]
        if isinstance(self.warning_threshold, Unset):
            warning_threshold = UNSET
        else:
            warning_threshold = self.warning_threshold

        last_window_start: Union[None, Unset, str]
        if isinstance(self.last_window_start, Unset):
            last_window_start = UNSET
        elif isinstance(self.last_window_start, datetime.datetime):
            last_window_start = self.last_window_start.isoformat()
        else:
            last_window_start = self.last_window_start

        run_until: Union[None, Unset, str]
        if isinstance(self.run_until, Unset):
            run_until = UNSET
        elif isinstance(self.run_until, datetime.datetime):
            run_until = self.run_until.isoformat()
        else:
            run_until = self.run_until

        last_run: Union[None, Unset, str]
        if isinstance(self.last_run, Unset):
            last_run = UNSET
        elif isinstance(self.last_run, datetime.datetime):
            last_run = self.last_run.isoformat()
        else:
            last_run = self.last_run

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "pipeline_id": pipeline_id,
                "pipeline_name": pipeline_name,
                "active": active,
                "status": status,
                "baseline": baseline,
                "window": window,
                "summarizer": summarizer,
                "alert_threshold": alert_threshold,
                "created_at": created_at,
                "workspace_id": workspace_id,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if warning_threshold is not UNSET:
            field_dict["warning_threshold"] = warning_threshold
        if last_window_start is not UNSET:
            field_dict["last_window_start"] = last_window_start
        if run_until is not UNSET:
            field_dict["run_until"] = run_until
        if last_run is not UNSET:
            field_dict["last_run"] = last_run

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assays_run_interactive_baseline_body_baseline_type_0 import (
            AssaysRunInteractiveBaselineBodyBaselineType0,
        )
        from ..models.assays_run_interactive_baseline_body_baseline_type_1 import (
            AssaysRunInteractiveBaselineBodyBaselineType1,
        )
        from ..models.assays_run_interactive_baseline_body_summarizer_type_0 import (
            AssaysRunInteractiveBaselineBodySummarizerType0,
        )
        from ..models.assays_run_interactive_baseline_body_summarizer_type_1 import (
            AssaysRunInteractiveBaselineBodySummarizerType1,
        )
        from ..models.assays_run_interactive_baseline_body_window import (
            AssaysRunInteractiveBaselineBodyWindow,
        )

        d = dict(src_dict)
        name = d.pop("name")

        pipeline_id = d.pop("pipeline_id")

        pipeline_name = d.pop("pipeline_name")

        active = d.pop("active")

        status = d.pop("status")

        def _parse_baseline(
            data: object,
        ) -> Union[
            "AssaysRunInteractiveBaselineBodyBaselineType0",
            "AssaysRunInteractiveBaselineBodyBaselineType1",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                baseline_type_0 = (
                    AssaysRunInteractiveBaselineBodyBaselineType0.from_dict(data)
                )

                return baseline_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            baseline_type_1 = AssaysRunInteractiveBaselineBodyBaselineType1.from_dict(
                data
            )

            return baseline_type_1

        baseline = _parse_baseline(d.pop("baseline"))

        window = AssaysRunInteractiveBaselineBodyWindow.from_dict(d.pop("window"))

        def _parse_summarizer(
            data: object,
        ) -> Union[
            "AssaysRunInteractiveBaselineBodySummarizerType0",
            "AssaysRunInteractiveBaselineBodySummarizerType1",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                summarizer_type_0 = (
                    AssaysRunInteractiveBaselineBodySummarizerType0.from_dict(data)
                )

                return summarizer_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            summarizer_type_1 = (
                AssaysRunInteractiveBaselineBodySummarizerType1.from_dict(data)
            )

            return summarizer_type_1

        summarizer = _parse_summarizer(d.pop("summarizer"))

        alert_threshold = d.pop("alert_threshold")

        created_at = isoparse(d.pop("created_at"))

        workspace_id = d.pop("workspace_id")

        def _parse_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_warning_threshold(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        warning_threshold = _parse_warning_threshold(d.pop("warning_threshold", UNSET))

        def _parse_last_window_start(
            data: object,
        ) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_window_start_type_0 = isoparse(data)

                return last_window_start_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        last_window_start = _parse_last_window_start(d.pop("last_window_start", UNSET))

        def _parse_run_until(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                run_until_type_0 = isoparse(data)

                return run_until_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        run_until = _parse_run_until(d.pop("run_until", UNSET))

        def _parse_last_run(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_run_type_0 = isoparse(data)

                return last_run_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        last_run = _parse_last_run(d.pop("last_run", UNSET))

        assays_run_interactive_baseline_body = cls(
            name=name,
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            active=active,
            status=status,
            baseline=baseline,
            window=window,
            summarizer=summarizer,
            alert_threshold=alert_threshold,
            created_at=created_at,
            workspace_id=workspace_id,
            id=id,
            warning_threshold=warning_threshold,
            last_window_start=last_window_start,
            run_until=run_until,
            last_run=last_run,
        )

        assays_run_interactive_baseline_body.additional_properties = d
        return assays_run_interactive_baseline_body

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
