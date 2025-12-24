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
    from ..models.assays_get_baseline_body_next_type_0 import (
        AssaysGetBaselineBodyNextType0,
    )


T = TypeVar("T", bound="AssaysGetBaselineBody")


@_attrs_define
class AssaysGetBaselineBody:
    """Request to retrieve an assay baseline.

    Attributes:
        pipeline_name (str):  Pipeline name.
        locations (list[str]):  Optional list of Edge Locations to filter on.
        workspace_id (Union[None, Unset, int]):  Workspace identifier.
        start (Union[None, Unset, str]):  Start date and time.
        end (Union[None, Unset, str]):  End date and time.
        model_name (Union[None, Unset, str]):  Model name.
        limit (Union[None, Unset, int]):  Maximum number of baselines to return.
        next_ (Union['AssaysGetBaselineBodyNextType0', None, Unset]):  Pagination object. Returned as part of previous
            requests.
    """

    pipeline_name: str
    locations: list[str]
    workspace_id: Union[None, Unset, int] = UNSET
    start: Union[None, Unset, str] = UNSET
    end: Union[None, Unset, str] = UNSET
    model_name: Union[None, Unset, str] = UNSET
    limit: Union[None, Unset, int] = UNSET
    next_: Union["AssaysGetBaselineBodyNextType0", None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.assays_get_baseline_body_next_type_0 import (
            AssaysGetBaselineBodyNextType0,
        )

        pipeline_name = self.pipeline_name

        locations = self.locations

        workspace_id: Union[None, Unset, int]
        if isinstance(self.workspace_id, Unset):
            workspace_id = UNSET
        else:
            workspace_id = self.workspace_id

        start: Union[None, Unset, str]
        if isinstance(self.start, Unset):
            start = UNSET
        else:
            start = self.start

        end: Union[None, Unset, str]
        if isinstance(self.end, Unset):
            end = UNSET
        else:
            end = self.end

        model_name: Union[None, Unset, str]
        if isinstance(self.model_name, Unset):
            model_name = UNSET
        else:
            model_name = self.model_name

        limit: Union[None, Unset, int]
        if isinstance(self.limit, Unset):
            limit = UNSET
        else:
            limit = self.limit

        next_: Union[None, Unset, dict[str, Any]]
        if isinstance(self.next_, Unset):
            next_ = UNSET
        elif isinstance(self.next_, AssaysGetBaselineBodyNextType0):
            next_ = self.next_.to_dict()
        else:
            next_ = self.next_

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "pipeline_name": pipeline_name,
                "locations": locations,
            }
        )
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id
        if start is not UNSET:
            field_dict["start"] = start
        if end is not UNSET:
            field_dict["end"] = end
        if model_name is not UNSET:
            field_dict["model_name"] = model_name
        if limit is not UNSET:
            field_dict["limit"] = limit
        if next_ is not UNSET:
            field_dict["next"] = next_

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assays_get_baseline_body_next_type_0 import (
            AssaysGetBaselineBodyNextType0,
        )

        d = dict(src_dict)
        pipeline_name = d.pop("pipeline_name")

        locations = cast(list[str], d.pop("locations"))

        def _parse_workspace_id(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        workspace_id = _parse_workspace_id(d.pop("workspace_id", UNSET))

        def _parse_start(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        start = _parse_start(d.pop("start", UNSET))

        def _parse_end(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        end = _parse_end(d.pop("end", UNSET))

        def _parse_model_name(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        model_name = _parse_model_name(d.pop("model_name", UNSET))

        def _parse_limit(data: object) -> Union[None, Unset, int]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, int], data)

        limit = _parse_limit(d.pop("limit", UNSET))

        def _parse_next_(
            data: object,
        ) -> Union["AssaysGetBaselineBodyNextType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                next_type_0 = AssaysGetBaselineBodyNextType0.from_dict(data)

                return next_type_0
            except:  # noqa: E722
                pass
            return cast(Union["AssaysGetBaselineBodyNextType0", None, Unset], data)

        next_ = _parse_next_(d.pop("next", UNSET))

        assays_get_baseline_body = cls(
            pipeline_name=pipeline_name,
            locations=locations,
            workspace_id=workspace_id,
            start=start,
            end=end,
            model_name=model_name,
            limit=limit,
            next_=next_,
        )

        assays_get_baseline_body.additional_properties = d
        return assays_get_baseline_body

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
