import enum
import json
from datetime import date, datetime

import pytest

from .object import deep_serialize


class _User:
    """dictable object"""

    def __init__(self, name: str):
        self.name = name

    def __iter__(self):
        for key in self.__dict__:
            yield key, getattr(self, key)


def test_deep_serialize__None():
    assert deep_serialize(None) is None


def test_deep_serialize__str():
    assert deep_serialize("a") == "a"


def test_deep_serialize__Enum():
    class MyEnum(enum.Enum):
        HELLO = "world"

    assert deep_serialize(MyEnum.HELLO) == "world"


def test_deep_serialize__int():
    assert deep_serialize(1) == 1
    assert deep_serialize(12345678987654321) == 12345678987654321


def test_deep_serialize__float():
    assert deep_serialize(1.3) == 1.3
    assert deep_serialize(0.01) == 0.01


def test_deep_serialize__date():
    assert deep_serialize(date(2020, 1, 2)) == "2020-01-02"


def test_deep_serialize__datetime():
    dt = datetime(1989, 8, 6, 10, 30)
    assert deep_serialize(dt) == "1989-08-06T10:30:00"


def test_deep_serialize__tuple():
    assert deep_serialize(tuple()) == []
    assert deep_serialize((1, "4")) == [1, "4"]


def test_deep_serialize__list():
    assert deep_serialize([]) == []
    assert deep_serialize([1, 2]) == [1, 2]
    assert deep_serialize([1.3, "4.3"]) == [1.3, "4.3"]


def test_deep_serialize__dict():
    assert deep_serialize({}) == {}
    assert deep_serialize({"a": 1}) == {"a": 1}


def test_deep_serialize__complex_object():
    user = _User(name="OK")
    serialized = deep_serialize(user)
    assert isinstance(serialized, dict)
    assert serialized["name"] == "OK"

    # Object non-dictable
    class Test:
        attr = 1

    with pytest.raises(ValueError):
        deep_serialize(Test())


def test_deep_serialize__nested():
    user1 = _User(name="1")
    user2 = _User(name="2")
    some_date = date(2021, 7, 1)

    input = [
        {
            "users": [user1, user2],
            "extracted_at": None,
            "level1": {"levels": [{2: 1}, user1]},
        },
        {"users": [], "extracted_at": some_date},
    ]

    serialized = deep_serialize(input)

    assert len(serialized) == 2

    d1, d2 = serialized

    d1_user_names = list(map(lambda x: x["name"], d1["users"]))
    assert d1_user_names == ["1", "2"]
    assert d1["level1"]["levels"][0] == {2: 1}
    assert d2["extracted_at"] == "2021-07-01"

    assert len(json.dumps(serialized)) > 1
