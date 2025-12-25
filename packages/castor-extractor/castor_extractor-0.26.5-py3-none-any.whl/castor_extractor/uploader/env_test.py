from .env import _parse_float, _parse_int


def test__parse_float():
    value = _parse_float("66", 33.0)
    assert value == 66.0
    assert isinstance(value, float)

    value = _parse_float(None, 66.0)
    assert value == 66.0
    assert isinstance(value, float)


def test__parse_int():
    value = _parse_int("66", 33)
    assert value == 66
    assert isinstance(value, int)

    value = _parse_int(None, 33)
    assert value == 33
    assert isinstance(value, int)
