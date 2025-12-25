import pytest

from .batch import batch_of_length


def test_batch_of_length():
    elements = ["a", "b", "c", "d", "e", "f", "g", "h"]
    result = list(batch_of_length(elements, 3))
    assert result == [
        ["a", "b", "c"],
        ["d", "e", "f"],
        ["g", "h"],
    ]

    result = list(batch_of_length(elements, 1000))
    assert result == [
        elements,
    ]

    result = list(batch_of_length(elements, 7))
    assert result == [
        ["a", "b", "c", "d", "e", "f", "g"],
        ["h"],
    ]

    with pytest.raises(AssertionError):
        list(batch_of_length(elements, -12))
