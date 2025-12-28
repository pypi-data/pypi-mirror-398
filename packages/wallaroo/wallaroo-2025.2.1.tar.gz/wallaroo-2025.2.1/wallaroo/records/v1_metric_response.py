# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = wallaroo_telemetry_metric_query_v1_from_dict(json.loads(json_string))

from typing import Any, List, Optional, TypeVar, Callable, Type, cast
from enum import Enum


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


class MetricQuery:
    """The alias for this query. Used for grouping metric results together"""

    alias: str
    """The prometheus query to run"""
    query: str

    def __init__(self, alias: str, query: str) -> None:
        self.alias = alias
        self.query = query

    @staticmethod
    def from_dict(obj: Any) -> "MetricQuery":
        assert isinstance(obj, dict)
        alias = from_str(obj.get("alias"))
        query = from_str(obj.get("query"))
        return MetricQuery(alias, query)

    def to_dict(self) -> dict:
        result: dict = {}
        result["alias"] = from_str(self.alias)
        result["query"] = from_str(self.query)
        return result


class QueryType(Enum):
    DAILY = "daily"
    INTERVAL = "interval"


class WallarooTelemetryMetricQueryV1:
    metrics: List[MetricQuery]
    query_type: QueryType
    """Post metrics on this minute, 0 is every minute."""
    run_on_minute: Optional[int]

    def __init__(
        self,
        metrics: List[MetricQuery],
        query_type: QueryType,
        run_on_minute: Optional[int],
    ) -> None:
        self.metrics = metrics
        self.query_type = query_type
        self.run_on_minute = run_on_minute

    @staticmethod
    def from_dict(obj: Any) -> "WallarooTelemetryMetricQueryV1":
        assert isinstance(obj, dict)
        metrics = from_list(MetricQuery.from_dict, obj.get("metrics"))
        query_type = QueryType(obj.get("query-type"))
        run_on_minute = from_union([from_int, from_none], obj.get("runOnMinute"))
        return WallarooTelemetryMetricQueryV1(metrics, query_type, run_on_minute)

    def to_dict(self) -> dict:
        result: dict = {}
        result["metrics"] = from_list(lambda x: to_class(MetricQuery, x), self.metrics)
        result["query-type"] = to_enum(QueryType, self.query_type)
        result["runOnMinute"] = from_union([from_int, from_none], self.run_on_minute)
        return result


def wallaroo_telemetry_metric_query_v1_from_dict(
    s: Any,
) -> WallarooTelemetryMetricQueryV1:
    return WallarooTelemetryMetricQueryV1.from_dict(s)


def wallaroo_telemetry_metric_query_v1_to_dict(
    x: WallarooTelemetryMetricQueryV1,
) -> Any:
    return to_class(WallarooTelemetryMetricQueryV1, x)
