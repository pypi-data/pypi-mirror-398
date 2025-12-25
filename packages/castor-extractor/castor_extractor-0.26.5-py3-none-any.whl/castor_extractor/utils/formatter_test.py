import io
import os

import pytest

from .formatter import (
    CsvFormatter,
    Formatter,
    JsonFormatter,
    remove_unsupported_byte,
    to_string_array,
)


def test__to_string_array():
    assert to_string_array('["foo"]') == ["foo"]
    assert to_string_array('["foo", "bar"]') == ["foo", "bar"]
    assert to_string_array('["1", "2"]') == ["1", "2"]

    with pytest.raises(ValueError):
        to_string_array("")  # empty string
        to_string_array('"foo"')  # missing brackets
        to_string_array('["foo", 3]')  # all elements must be string


SAMPLE_KEYS = (
    "id",
    "first_name",
    "last_name",
    "email",
    "ip_address",
    "phone_number",
    "timezone",
    "has_subscribed",
)

SAMPLE_SIZE = 50

SAMPLE_FILE = "formatter_test"


def _test(formatter: Formatter) -> None:
    root = os.path.dirname(__file__)
    path = os.path.join(root, f"{SAMPLE_FILE}.{formatter.extension()}")
    with open(path) as file:
        rows = list(formatter.deserialize(file))
        first = rows[0]

        assert len(rows) == SAMPLE_SIZE
        assert tuple(first.keys()) == SAMPLE_KEYS

        with io.StringIO() as f:
            # writing CSV to buffer
            formatter.serialize(f, rows)
            # reset the buffer position to the beginning before reading
            f.seek(0)
            # deserialize(serialize(x)) == x
            assert list(formatter.deserialize(f)) == rows


def test__csv_formatter():
    formatter = CsvFormatter()
    _test(formatter)


def test__json_formatter():
    formatter = JsonFormatter()
    _test(formatter)


@pytest.mark.parametrize(
    "element, expected_output",
    [(1, 1), ("foo", "foo"), ("bar\x00bie", "barbie")],
)
def test__remove_unsupported_byte(element, expected_output):
    cleaned = remove_unsupported_byte(element)
    assert cleaned == expected_output
