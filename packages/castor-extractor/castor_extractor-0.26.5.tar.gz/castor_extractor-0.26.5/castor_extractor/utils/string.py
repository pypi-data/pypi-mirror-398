import ast
import re
import string
from typing import TypeVar

_ALPHANUMERIC_REGEX = r"^\w+$"
_SYMBOLS = "[]{}()"

T = TypeVar("T", bytes, str, int, float, bool, None)


def _clean(input_: str) -> str:
    """
    Clean the input to reduce the number of cases:
    - remove trailing white spaces
    - remove carriage returns '\n'
    - remove lists symbols ( ) [ ] { }
      "  [  'a', 'b'  ]  " => "'a', 'b'"
      ['a', 'b'] ~ {'a', 'b'} ~ ('a', 'b') => 'a', 'b'
      ['a'] ~ {'a'} ~ ('a') => 'a'
      a => 'a'
    """
    # remove trailing symbols and whitespaces
    cleaned = input_.strip(_SYMBOLS + string.whitespace)
    cleaned = cleaned.replace("\n", "")

    # handle unquoted singleton: _clean(foo) == 'foo'
    if re.match(_ALPHANUMERIC_REGEX, cleaned):
        cleaned = f"'{cleaned}'"

    return cleaned


def string_to_tuple(input_: str) -> tuple[str, ...]:
    """
    Parse the given string and returns the corresponding Tuple of strings

    Supported formats:
    - list ['a', 'b']
    - tuples ('a', 'b')
    - sets {'a', 'b', 'c'}

    Extra coma allowed: ['a', 'b', ]
    Carriage returns allowed: [
        'a',
        'b'
    ]
    Empty list allowed: []
    Singleton allowed: 'a'
    Multiple types allowed: ['foo', 100, 19.8]
    Comas between double quotes allowed: "Hi, there" => ("Hi, there", ...)

    Not supported:
    - unbalanced quotes: "a", b"
    - Multiple strings without quotes: a, b
    """
    cleaned = _clean(input_)
    if not cleaned:
        # support empty string
        return tuple()

    parsed = ast.literal_eval(cleaned)

    # list or tuple containing several elements
    if isinstance(parsed, (tuple, list, set)):
        return tuple(str(element) for element in parsed)

    # float or integer singleton
    if isinstance(parsed, (int, float)):
        return (str(parsed),)

    # string singleton
    if isinstance(parsed, str):  # single element
        return (parsed,)

    raise ValueError(f"Could not parse input to Tuple[String,...]: {input_}")


def decode_when_bytes(value: T, encoding: str = "utf-8") -> T | str:
    """
    Decode bytes using the given encoding, if no encoding are given utf-8 will
    be used by default.
    If value is not bytes, then the value is returned as-is.
    """
    if isinstance(value, bytes):
        return value.decode(encoding)

    return value
