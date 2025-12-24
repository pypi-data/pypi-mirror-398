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
    from ..models.run_frequency_type_0 import RunFrequencyType0
    from ..models.run_frequency_type_1 import RunFrequencyType1


T = TypeVar("T", bound="Scheduling")


@_attrs_define
class Scheduling:
    """Controls how an assay is scheduled.
    We should be able to specify the start, end, and frequency.

        Attributes:
            first_run (datetime.datetime): The first time that the assay will **run**.
                This means that the first AssayResult will be calculated for
                inferences after `first_run - window.width` date and before and including `first_run`

                All assays are required to start at a specific time, default to now.
            run_frequency (Union['RunFrequencyType0', 'RunFrequencyType1']):
            end (Union[None, Unset, datetime.datetime]): End time of the assay. After this time, no more runs will be made.
                A None value indicates that this assay will run indefinitely.
    """

    first_run: datetime.datetime
    run_frequency: Union["RunFrequencyType0", "RunFrequencyType1"]
    end: Union[None, Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.run_frequency_type_0 import RunFrequencyType0

        first_run = self.first_run.isoformat()

        run_frequency: dict[str, Any]
        if isinstance(self.run_frequency, RunFrequencyType0):
            run_frequency = self.run_frequency.to_dict()
        else:
            run_frequency = self.run_frequency.to_dict()

        end: Union[None, Unset, str]
        if isinstance(self.end, Unset):
            end = UNSET
        elif isinstance(self.end, datetime.datetime):
            end = self.end.isoformat()
        else:
            end = self.end

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "first_run": first_run,
                "run_frequency": run_frequency,
            }
        )
        if end is not UNSET:
            field_dict["end"] = end

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_frequency_type_0 import RunFrequencyType0
        from ..models.run_frequency_type_1 import RunFrequencyType1

        d = dict(src_dict)
        first_run = isoparse(d.pop("first_run"))

        def _parse_run_frequency(
            data: object,
        ) -> Union["RunFrequencyType0", "RunFrequencyType1"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_run_frequency_type_0 = RunFrequencyType0.from_dict(
                    data
                )

                return componentsschemas_run_frequency_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_run_frequency_type_1 = RunFrequencyType1.from_dict(data)

            return componentsschemas_run_frequency_type_1

        run_frequency = _parse_run_frequency(d.pop("run_frequency"))

        def _parse_end(data: object) -> Union[None, Unset, datetime.datetime]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_type_0 = isoparse(data)

                return end_type_0
            except:  # noqa: E722
                pass
            return cast(Union[None, Unset, datetime.datetime], data)

        end = _parse_end(d.pop("end", UNSET))

        scheduling = cls(
            first_run=first_run,
            run_frequency=run_frequency,
            end=end,
        )

        scheduling.additional_properties = d
        return scheduling

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
