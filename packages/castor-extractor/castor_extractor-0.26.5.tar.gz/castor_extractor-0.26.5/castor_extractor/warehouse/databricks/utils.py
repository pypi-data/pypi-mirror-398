from collections.abc import Iterable
from datetime import date

from ...utils import at_midnight
from ..abstract import TimeFilter

_DEFAULT_HOUR_MIN = 0
_DEFAULT_HOUR_MAX = 23
_NUM_HOURS_IN_A_DAY = 24


def _day_hour_to_epoch_ms(day: date, hour: int) -> int:
    return int(at_midnight(day).timestamp() * 1000) + (hour * 3600 * 1000)


def build_path(
    row: dict,
    keys: list[str],
) -> str:
    """
    format an asset's path:
    - picks the given keys from dict
    - join keys with a dot "."
    """
    key_values = [row[key] for key in keys]
    return ".".join(key_values)


def tag_label(row: dict) -> str:
    """
    format the tag's label:
    - {key:value} when the value is not empty
    - {key} otherwise
    """
    tag_name = row["tag_name"]
    tag_value = row["tag_value"]
    if not tag_value:
        return tag_name
    return f"{tag_name}:{tag_value}"


def _time_filter_payload(start_time_ms: int, end_time_ms: int) -> dict:
    return {
        "filter_by": {
            "query_start_time_range": {
                "end_time_ms": end_time_ms,
                "start_time_ms": start_time_ms,
            }
        }
    }


def hourly_time_filters(time_filter: TimeFilter | None) -> Iterable[dict]:
    """time filters to retrieve Databricks' queries: 1h duration each"""
    # define an explicit time window
    if not time_filter:
        time_filter = TimeFilter.default()

    assert time_filter  # for mypy

    hour_min = time_filter.hour_min
    hour_max = time_filter.hour_max
    day = time_filter.day
    if hour_min is None or hour_max is None:  # fallback to an entire day
        hour_min, hour_max = _DEFAULT_HOUR_MIN, _DEFAULT_HOUR_MAX

    for index in range(hour_min, min(hour_max + 1, _NUM_HOURS_IN_A_DAY)):
        start_time_ms = _day_hour_to_epoch_ms(day, index)
        end_time_ms = _day_hour_to_epoch_ms(day, index + 1)
        yield _time_filter_payload(start_time_ms, end_time_ms)
