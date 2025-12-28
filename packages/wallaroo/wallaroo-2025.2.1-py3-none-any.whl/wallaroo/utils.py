import functools
import os
import re
from datetime import datetime, timezone
from typing import Optional, TextIO, TypeVar, Union

import numpy as np
import pyarrow as pa  # type: ignore

from .object import InvalidNameError

ASSAYS_V2_ENABLED = "ASSAYS_V2_ENABLED"

DEFAULT_ARROW_FILE_SUFFIX = "arrow"
DEFAULT_JSON_FILE_SUFFIX = "json"


def is_assays_v2_enabled():
    return os.getenv(ASSAYS_V2_ENABLED, "true").lower() == "true"


def flatten_np_array_columns(df, col):
    if isinstance(df[col][0], np.ndarray):
        return df[col].apply(lambda x: np.array(x).ravel())
    else:
        return df[col]


def convert_ndarray_batch_to_arrow(arr):
    batch_size = arr.shape[0]
    inner_size = functools.reduce(lambda a, b: a * b, arr.shape[1:])
    offsets = range(0, (batch_size * inner_size) + 1, inner_size)
    return pa.ListArray.from_arrays(offsets, arr.reshape([batch_size * inner_size]))


def generate_file_name(
    directory: str, file_prefix: str, file_num: int, file_suffix: str
) -> str:
    return os.path.join(directory, f"{file_prefix}-{file_num}.{file_suffix}")


def create_new_arrow_file(
    directory: str, file_num: int, file_prefix: str, file_suffix: str, schema: pa.Schema
) -> pa.RecordBatchFileWriter:
    filepath = generate_file_name(directory, file_prefix, file_num, file_suffix)
    sink = pa.OSFile(filepath, "wb")
    writer = pa.ipc.new_file(sink, schema)
    return writer


def create_new_json_file(
    directory: str, file_num: int, file_prefix: str, file_suffix: str
) -> TextIO:
    filepath = generate_file_name(directory, file_prefix, file_num, file_suffix)
    sink = open(filepath, "w")
    return sink


def create_new_file(
    directory: str,
    file_num: int,
    file_prefix: str,
    schema: Optional[pa.Schema] = None,
    arrow: Optional[bool] = False,
) -> Union[pa.RecordBatchFileWriter, TextIO]:
    if arrow:
        return create_new_arrow_file(
            directory, file_num, file_prefix, DEFAULT_ARROW_FILE_SUFFIX, schema
        )
    else:
        return create_new_json_file(
            directory, file_num, file_prefix, DEFAULT_JSON_FILE_SUFFIX
        )


def write_to_file(
    record_batch: Union[pa.RecordBatch, str],
    writer: Union[pa.RecordBatchFileWriter, TextIO],
) -> None:
    if isinstance(record_batch, pa.RecordBatch):
        writer.write_batch(record_batch)  # type: ignore
    elif isinstance(record_batch, str):
        writer.write(record_batch)  # type: ignore
    else:
        raise TypeError(
            f"write_to_file() expects pa.RecordBatch or str, got {type(record_batch)}"
        )


# Cache for the validation regex
_dns_req = None


def dns_compliant(name: str):
    """Returns true if a string is compliant with DNS label name requirement to
    ensure it can be a part of a full DNS host name
    """
    global _dns_req
    if not _dns_req:
        # https://en.wikipedia.org/wiki/Domain_Name_System
        _dns_req = re.compile("^[a-zA-Z][a-zA-Z0-9-]*[a-zA-Z0-9]*$")

    return len(name) < 64 and _dns_req.match(name) is not None and name[-1] != "-"


def require_dns_compliance(name: str):
    """Validates that 'name' complies with DNS naming requirements or raises an exception"""
    if not dns_compliant(name):
        raise InvalidNameError(
            name, "must be DNS-compatible (ASCII alpha-numeric plus dash (-))"
        )


T = TypeVar("T")


# Removes the Optional wrapper.
def _unwrap(v: Optional[T]) -> T:
    """Simple function to placate pylance"""
    if v:
        return v
    raise Exception("Expected a value in forced unwrap")


def _ensure_tz(d: datetime) -> datetime:
    """Ensure the date it tz aware. If naive assume it is in utc."""
    if d.tzinfo:
        return d
    else:
        return d.astimezone(tz=timezone.utc)
