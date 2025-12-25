from datetime import date

from freezegun import freeze_time

from ..abstract import TimeFilter
from .utils import (
    _day_hour_to_epoch_ms,
    build_path,
    hourly_time_filters,
    tag_label,
)


def test_build_path():
    row = {
        "bigflo": "oli",
        "laurel": "hardy",
        "dupond": "dupont",
    }
    keys = ["laurel", "dupond"]
    assert build_path(row, keys) == "hardy.dupont"


def test_tag_label():
    row = {
        "tag_name": "marketplace",
        "tag_value": "",
    }
    assert tag_label(row) == "marketplace"

    row = {
        "tag_name": "fi",
        "tag_value": "fou",
    }
    assert tag_label(row) == "fi:fou"


def test__day_hour_to_epoch_ms():
    assert _day_hour_to_epoch_ms(date(2023, 2, 14), 14) == 1676383200000


@freeze_time("2023-7-4")
def test_hourly_time_filters():
    # default is yesterday
    default_filters = [f for f in hourly_time_filters(None)]

    assert len(default_filters) == 24  # number of hours in a day

    first = default_filters[0]
    start = first["filter_by"]["query_start_time_range"]["start_time_ms"]
    last = default_filters[-1]
    end = last["filter_by"]["query_start_time_range"]["end_time_ms"]
    assert start == 1688342400000  # July 3, 2023 12:00:00 AM GMT
    assert end == 1688428800000  # July 4, 2023 12:00:00 AM GMT

    # custom time (from execution_date in DAG for example)
    time_filter = TimeFilter(day=date(2020, 10, 15))
    custom_filters = [f for f in hourly_time_filters(time_filter)]

    assert len(custom_filters) == 24

    first = custom_filters[0]
    start = first["filter_by"]["query_start_time_range"]["start_time_ms"]
    last = custom_filters[-1]
    end = last["filter_by"]["query_start_time_range"]["end_time_ms"]
    assert start == 1602720000000  # Oct 15, 2020 12:00:00 AM
    assert end == 1602806400000  # Oct 16, 2020 12:00:00 AM

    # hourly extraction: note that hour_min == hour_max
    hourly = TimeFilter(day=date(2023, 4, 14), hour_min=4, hour_max=4)
    hourly_filters = [f for f in hourly_time_filters(hourly)]
    expected_hourly = [
        {
            "filter_by": {
                "query_start_time_range": {
                    "end_time_ms": 1681448400000,  # April 14, 2023 5:00:00 AM
                    "start_time_ms": 1681444800000,  # April 14, 2023 4:00:00 AM
                }
            }
        }
    ]
    assert hourly_filters == expected_hourly
