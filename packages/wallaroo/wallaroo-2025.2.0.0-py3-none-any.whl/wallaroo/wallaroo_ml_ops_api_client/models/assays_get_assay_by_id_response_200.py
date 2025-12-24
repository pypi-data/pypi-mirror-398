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
    from ..models.assays_get_assay_by_id_response_200_baseline_type_0 import (
        AssaysGetAssayByIdResponse200BaselineType0,
    )
    from ..models.assays_get_assay_by_id_response_200_baseline_type_1 import (
        AssaysGetAssayByIdResponse200BaselineType1,
    )
    from ..models.assays_get_assay_by_id_response_200_summarizer_type_0 import (
        AssaysGetAssayByIdResponse200SummarizerType0,
    )
    from ..models.assays_get_assay_by_id_response_200_summarizer_type_1 import (
        AssaysGetAssayByIdResponse200SummarizerType1,
    )
    from ..models.assays_get_assay_by_id_response_200_window_type_0 import (
        AssaysGetAssayByIdResponse200WindowType0,
    )


T = TypeVar("T", bound="AssaysGetAssayByIdResponse200")


@_attrs_define
class AssaysGetAssayByIdResponse200:
    """Response type for /assays/get_by_id

    Attributes:
        id (int):  Assay identifier.
        name (str):  Assay name.
        active (bool):  Flag indicating whether the assay is active.
        status (str):  Assay status.
        alert_threshold (float):  Alert threshold.
        pipeline_id (int):  Pipeline identifier.
        pipeline_name (str):  Pipeline name.
        workspace_id (int):  Workspace identifier.
        workspace_name (str): Workspace name.
        next_run (str):  Date and time of the next run.
        warning_threshold (Union[None, Unset, float]):  Warning threshold.
        last_run (Union[None, Unset, str]):  Date and time of the last run.
        run_until (Union[None, Unset, str]):  Date and time until which the assay is to run.
        created_at (Union[None, Unset, str]):  Creation date and time of the assay.
        updated_at (Union[None, Unset, str]):  Date and time the assay was last updated.
        baseline (Union['AssaysGetAssayByIdResponse200BaselineType0', 'AssaysGetAssayByIdResponse200BaselineType1',
            None, Unset]):  Options describing the baseline summary used for the assay
        window (Union['AssaysGetAssayByIdResponse200WindowType0', None, Unset]):  Options describing the time range
            tested by the assay
        summarizer (Union['AssaysGetAssayByIdResponse200SummarizerType0',
            'AssaysGetAssayByIdResponse200SummarizerType1', None, Unset]):  Options describing the types of analysis done by
            the assay
    """

    id: int
    name: str
    active: bool
    status: str
    alert_threshold: float
    pipeline_id: int
    pipeline_name: str
    workspace_id: int
    workspace_name: str
    next_run: str
    warning_threshold: Union[None, Unset, float] = UNSET
    last_run: Union[None, Unset, str] = UNSET
    run_until: Union[None, Unset, str] = UNSET
    created_at: Union[None, Unset, str] = UNSET
    updated_at: Union[None, Unset, str] = UNSET
    baseline: Union[
        "AssaysGetAssayByIdResponse200BaselineType0",
        "AssaysGetAssayByIdResponse200BaselineType1",
        None,
        Unset,
    ] = UNSET
    window: Union["AssaysGetAssayByIdResponse200WindowType0", None, Unset] = UNSET
    summarizer: Union[
        "AssaysGetAssayByIdResponse200SummarizerType0",
        "AssaysGetAssayByIdResponse200SummarizerType1",
        None,
        Unset,
    ] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.assays_get_assay_by_id_response_200_baseline_type_0 import (
            AssaysGetAssayByIdResponse200BaselineType0,
        )
        from ..models.assays_get_assay_by_id_response_200_baseline_type_1 import (
            AssaysGetAssayByIdResponse200BaselineType1,
        )
        from ..models.assays_get_assay_by_id_response_200_summarizer_type_0 import (
            AssaysGetAssayByIdResponse200SummarizerType0,
        )
        from ..models.assays_get_assay_by_id_response_200_summarizer_type_1 import (
            AssaysGetAssayByIdResponse200SummarizerType1,
        )
        from ..models.assays_get_assay_by_id_response_200_window_type_0 import (
            AssaysGetAssayByIdResponse200WindowType0,
        )

        id = self.id

        name = self.name

        active = self.active

        status = self.status

        alert_threshold = self.alert_threshold

        pipeline_id = self.pipeline_id

        pipeline_name = self.pipeline_name

        workspace_id = self.workspace_id

        workspace_name = self.workspace_name

        next_run = self.next_run

        warning_threshold: Union[None, Unset, float]
        if isinstance(self.warning_threshold, Unset):
            warning_threshold = UNSET
        else:
            warning_threshold = self.warning_threshold

        last_run: Union[None, Unset, str]
        if isinstance(self.last_run, Unset):
            last_run = UNSET
        else:
            last_run = self.last_run

        run_until: Union[None, Unset, str]
        if isinstance(self.run_until, Unset):
            run_until = UNSET
        else:
            run_until = self.run_until

        created_at: Union[None, Unset, str]
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        updated_at: Union[None, Unset, str]
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = self.updated_at

        baseline: Union[None, Unset, dict[str, Any]]
        if isinstance(self.baseline, Unset):
            baseline = UNSET
        elif isinstance(self.baseline, AssaysGetAssayByIdResponse200BaselineType0):
            baseline = self.baseline.to_dict()
        elif isinstance(self.baseline, AssaysGetAssayByIdResponse200BaselineType1):
            baseline = self.baseline.to_dict()
        else:
            baseline = self.baseline

        window: Union[None, Unset, dict[str, Any]]
        if isinstance(self.window, Unset):
            window = UNSET
        elif isinstance(self.window, AssaysGetAssayByIdResponse200WindowType0):
            window = self.window.to_dict()
        else:
            window = self.window

        summarizer: Union[None, Unset, dict[str, Any]]
        if isinstance(self.summarizer, Unset):
            summarizer = UNSET
        elif isinstance(self.summarizer, AssaysGetAssayByIdResponse200SummarizerType0):
            summarizer = self.summarizer.to_dict()
        elif isinstance(self.summarizer, AssaysGetAssayByIdResponse200SummarizerType1):
            summarizer = self.summarizer.to_dict()
        else:
            summarizer = self.summarizer

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "active": active,
                "status": status,
                "alert_threshold": alert_threshold,
                "pipeline_id": pipeline_id,
                "pipeline_name": pipeline_name,
                "workspace_id": workspace_id,
                "workspace_name": workspace_name,
                "next_run": next_run,
            }
        )
        if warning_threshold is not UNSET:
            field_dict["warning_threshold"] = warning_threshold
        if last_run is not UNSET:
            field_dict["last_run"] = last_run
        if run_until is not UNSET:
            field_dict["run_until"] = run_until
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if baseline is not UNSET:
            field_dict["baseline"] = baseline
        if window is not UNSET:
            field_dict["window"] = window
        if summarizer is not UNSET:
            field_dict["summarizer"] = summarizer

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assays_get_assay_by_id_response_200_baseline_type_0 import (
            AssaysGetAssayByIdResponse200BaselineType0,
        )
        from ..models.assays_get_assay_by_id_response_200_baseline_type_1 import (
            AssaysGetAssayByIdResponse200BaselineType1,
        )
        from ..models.assays_get_assay_by_id_response_200_summarizer_type_0 import (
            AssaysGetAssayByIdResponse200SummarizerType0,
        )
        from ..models.assays_get_assay_by_id_response_200_summarizer_type_1 import (
            AssaysGetAssayByIdResponse200SummarizerType1,
        )
        from ..models.assays_get_assay_by_id_response_200_window_type_0 import (
            AssaysGetAssayByIdResponse200WindowType0,
        )

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        active = d.pop("active")

        status = d.pop("status")

        alert_threshold = d.pop("alert_threshold")

        pipeline_id = d.pop("pipeline_id")

        pipeline_name = d.pop("pipeline_name")

        workspace_id = d.pop("workspace_id")

        workspace_name = d.pop("workspace_name")

        next_run = d.pop("next_run")

        def _parse_warning_threshold(data: object) -> Union[None, Unset, float]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, float], data)

        warning_threshold = _parse_warning_threshold(d.pop("warning_threshold", UNSET))

        def _parse_last_run(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        last_run = _parse_last_run(d.pop("last_run", UNSET))

        def _parse_run_until(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        run_until = _parse_run_until(d.pop("run_until", UNSET))

        def _parse_created_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        def _parse_updated_at(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        def _parse_baseline(
            data: object,
        ) -> Union[
            "AssaysGetAssayByIdResponse200BaselineType0",
            "AssaysGetAssayByIdResponse200BaselineType1",
            None,
            Unset,
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                baseline_type_0 = AssaysGetAssayByIdResponse200BaselineType0.from_dict(
                    data
                )

                return baseline_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                baseline_type_1 = AssaysGetAssayByIdResponse200BaselineType1.from_dict(
                    data
                )

                return baseline_type_1
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "AssaysGetAssayByIdResponse200BaselineType0",
                    "AssaysGetAssayByIdResponse200BaselineType1",
                    None,
                    Unset,
                ],
                data,
            )

        baseline = _parse_baseline(d.pop("baseline", UNSET))

        def _parse_window(
            data: object,
        ) -> Union["AssaysGetAssayByIdResponse200WindowType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                window_type_0 = AssaysGetAssayByIdResponse200WindowType0.from_dict(data)

                return window_type_0
            except:  # noqa: E722
                pass
            return cast(
                Union["AssaysGetAssayByIdResponse200WindowType0", None, Unset], data
            )

        window = _parse_window(d.pop("window", UNSET))

        def _parse_summarizer(
            data: object,
        ) -> Union[
            "AssaysGetAssayByIdResponse200SummarizerType0",
            "AssaysGetAssayByIdResponse200SummarizerType1",
            None,
            Unset,
        ]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                summarizer_type_0 = (
                    AssaysGetAssayByIdResponse200SummarizerType0.from_dict(data)
                )

                return summarizer_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                summarizer_type_1 = (
                    AssaysGetAssayByIdResponse200SummarizerType1.from_dict(data)
                )

                return summarizer_type_1
            except:  # noqa: E722
                pass
            return cast(
                Union[
                    "AssaysGetAssayByIdResponse200SummarizerType0",
                    "AssaysGetAssayByIdResponse200SummarizerType1",
                    None,
                    Unset,
                ],
                data,
            )

        summarizer = _parse_summarizer(d.pop("summarizer", UNSET))

        assays_get_assay_by_id_response_200 = cls(
            id=id,
            name=name,
            active=active,
            status=status,
            alert_threshold=alert_threshold,
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            next_run=next_run,
            warning_threshold=warning_threshold,
            last_run=last_run,
            run_until=run_until,
            created_at=created_at,
            updated_at=updated_at,
            baseline=baseline,
            window=window,
            summarizer=summarizer,
        )

        assays_get_assay_by_id_response_200.additional_properties = d
        return assays_get_assay_by_id_response_200

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
