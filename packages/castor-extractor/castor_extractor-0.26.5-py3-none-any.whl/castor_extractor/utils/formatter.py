"""convert files to csv"""

import csv
import ctypes
import json
import logging
import re
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Sequence
from datetime import date, datetime
from enum import Enum
from typing import IO, Any, Union
from uuid import UUID

from ..types import CsvOptions

CSV_OPTIONS: CsvOptions = {
    "delimiter": ",",
    # bigquery import requires explicit quoting
    "quoting": csv.QUOTE_ALL,
    "quotechar": '"',
}

CSV_FIELD_SIZE_MB = 100

ScalarValue = Union[int, float, None, str]

logger = logging.getLogger(__name__)


def _header(row: dict) -> Sequence[str]:
    return [str(r) for r in row.keys()]


def _scalar(value: Any) -> ScalarValue:
    if isinstance(value, str):
        if "\x00" in value:  # infrequent error caused by bad encoding
            value = remove_unsupported_byte(value)
            logger.warning("Removed unsupported byte to write to csv")
            return value

        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    # fallback
    return str(value)


def _row(header: Sequence[str], row: dict) -> list[ScalarValue]:
    return [_scalar(row.get(h)) for h in header]


def remove_unsupported_byte(element: ScalarValue) -> ScalarValue:
    if not isinstance(element, str):
        return element

    return re.sub("\x00", "", element)


def to_string_array(arr_json: str) -> list[str]:
    """
    Converts a JSON-serialized string array value as a string to a list
    Ex: '["items","count"]' to ["items", "order"]
    """

    if not arr_json.startswith("[") or not arr_json.endswith("]"):
        raise ValueError(f"Cannot deserialize (not an array): {arr_json}")

    try:
        array = json.loads(arr_json)
    except ValueError:
        raise ValueError(f"Cannot deserialize (not a JSON): {arr_json}")

    if not all(isinstance(el, str) for el in array):
        raise ValueError(f"Not an array of strings: {arr_json}")

    return array


def to_csv(buffer: IO[str], data: Iterable[dict]) -> bool:
    """convert data as list of dicts to CSV string"""

    writer = csv.writer(buffer, **CSV_OPTIONS)

    header = None
    for row in data:
        # write header once
        if not header:
            header = _header(row)
            writer.writerow(header)
        converted = _row(header, row)
        writer.writerow(converted)
    return True


def from_csv(buffer: IO[str]) -> Iterator[dict]:
    """convert data as from a CSV string to list of dict"""
    try:
        reader = csv.reader(buffer, **CSV_OPTIONS)
        header: list[str] = []
        for row in reader:
            if not header:
                header = list(row)
                continue
            yield {h: v for h, v in zip(header, row)}
    finally:
        # closing of the file must happen after all iterations
        buffer.close()


class Formatter(ABC):
    """
    Abstract class to Serialize/Deserialize to any format
    """

    @abstractmethod
    def extension(self) -> str:
        pass

    @staticmethod
    @abstractmethod
    def serialize(buffer: IO[str], data: Iterable[dict]) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def deserialize(data: IO[str]) -> Iterator[dict]:
        pass


def _set_csv_field_size_limit(target_limit_mb: int) -> None:
    """
    Safely set the maximum CSV field size limit across platforms.

    This function wraps `csv.field_size_limit()` to avoid `OverflowError` on
    Windows, where the maximum C long is only 32 bits (2^31 - 1). On Linux and
    macOS, the C long is typically 64 bits, allowing much larger values.

    The requested limit is specified in megabytes and converted to bytes.

    It is then clamped to the maximum value supported by:
      - the current platform's C long
      - Python's `sys.maxsize`
      - the requested target limit
    """
    target_limit_bytes = target_limit_mb * 1024**2

    # max value of C long for the current platform
    platform_c_long = (1 << (8 * ctypes.sizeof(ctypes.c_long) - 1)) - 1

    limit_bytes = min(target_limit_bytes, sys.maxsize, platform_c_long)

    csv.field_size_limit(limit_bytes)


class CsvFormatter(Formatter):
    """
    Serialize/Deserialize CSV
    """

    def extension(self) -> str:
        return "csv"

    # increase the size limit (some fields are very large)
    _set_csv_field_size_limit(target_limit_mb=CSV_FIELD_SIZE_MB)

    @staticmethod
    def serialize(buffer: IO[str], data: Iterable[dict]) -> bool:
        return to_csv(buffer, data)

    @staticmethod
    def deserialize(buffer: IO[str]) -> Iterator[dict]:
        return from_csv(buffer)


class CustomEncoder(json.JSONEncoder):
    """supersedes the default encoder to handle additional types"""

    def default(self, obj: object) -> object:
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.name
        return json.JSONEncoder.default(self, obj)


class JsonFormatter(Formatter):
    """
    Serialize/Deserialize JSON
    """

    def extension(self) -> str:
        return "json"

    @staticmethod
    def serialize(buffer: IO[str], data: Iterable[dict]) -> bool:
        try:
            json.dump(data, fp=buffer, cls=CustomEncoder)
            return True
        except ValueError:
            return False

    @staticmethod
    def deserialize(buffer: IO[str]) -> Iterator[dict]:
        try:
            data = json.load(buffer)
            return data
        finally:
            buffer.close()
