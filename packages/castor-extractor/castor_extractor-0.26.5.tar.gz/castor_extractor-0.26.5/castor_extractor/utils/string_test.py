import pytest

from .string import decode_when_bytes, string_to_tuple


def _test(symbols: str, input_: str) -> tuple[str, ...]:
    return string_to_tuple(symbols[0] + input_ + symbols[1])


def test__string_to_tuple():
    """Test method string_to_tuple"""

    # loop on supported symbols surrounding elements
    for symbols in ("[]", "{}", "()", "  "):
        # empty list, set, tuple and empty string
        # [], {}, (), ''
        assert _test(symbols, "") == tuple()

        # single string, simple quotes
        assert _test(symbols, "'a'") == ("a",)
        # single string, double quotes
        assert _test(symbols, '"a"') == ("a",)
        # single string, no quotes
        assert _test(symbols, "a") == ("a",)
        # single strings, double quotes and coma inside
        assert _test(symbols, '"Hi, how are you?"') == ("Hi, how are you?",)

        # multiple strings, simple quotes
        assert _test(symbols, "'a', 'b'") == ("a", "b")
        # multiple strings, double quotes
        assert _test(symbols, '"a", "b"') == ("a", "b")
        # multiple strings, double quotes and coma inside
        assert _test(symbols, '"Hi, how are you?", "I am fine, thanks!"') == (
            "Hi, how are you?",
            "I am fine, thanks!",
        )

        # multiple strings + carriage returns
        value = """ [
            'a',
            'b'
        ]
        """
        assert _test(symbols, value) == ("a", "b")

        # multiple strings + extra coma
        assert _test(symbols, "'a', 'b',") == ("a", "b")

        # single integer
        assert _test(symbols, "1") == ("1",)
        # multiple integers
        assert _test(symbols, "1, 2, 3") == ("1", "2", "3")

        # single float
        assert _test(symbols, "3.14") == ("3.14",)
        # multiple floats
        assert _test(symbols, "3.14, -2.0") == ("3.14", "-2.0")

        # mixed data types
        assert _test(symbols, "'a', 12, -5.7") == ("a", "12", "-5.7")

        with pytest.raises(SyntaxError):
            # unbalanced quotes
            _test(symbols, '"a", b"')
        with pytest.raises(ValueError):
            # multiple strings, no quotes
            _test(symbols, "a, b")


def test_decode_when_bytes():
    assert decode_when_bytes("same") == "same"
    assert decode_when_bytes(b"\xc3\xa9\xc3\xa0\xc3\xb4") == "éàô"
    assert not decode_when_bytes(None)
    assert decode_when_bytes(1) == 1
    assert decode_when_bytes(1.34) == 1.34
    assert decode_when_bytes(True)
