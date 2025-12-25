from .fields import format_fields


def test_format_fields__string():
    fields = "a"

    assert format_fields(fields) == "a"


def test_format_fields__strings():
    fields = ("a", "b", "c", "d")

    assert format_fields(fields) == "a, b, c, d"


def test_format_fields__dict():
    fields = {"a": ("1", "2")}

    assert format_fields(fields) == "a(1, 2)"


def test_format_fields__dicts():
    fields = ({"a": ("1", "2")}, {"b": ("3", "4", "5")})

    assert format_fields(fields) == "a(1, 2), b(3, 4, 5)"


def test_format_fields__nested_dict():
    fields = {"a": {"b": {"c": ("1", "2")}}}

    assert format_fields(fields) == "a(b(c(1, 2)))"


def test_format_fields__wraped_tuple():
    fields = (("1",), ({"a": (("4",),)}))

    assert format_fields(fields) == "1, a(4)"
