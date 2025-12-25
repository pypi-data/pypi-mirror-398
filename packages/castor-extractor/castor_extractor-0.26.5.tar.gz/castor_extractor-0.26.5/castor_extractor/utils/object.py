from collections.abc import Iterator
from datetime import date, datetime
from enum import Enum
from typing import Any, overload
from uuid import UUID

from .type import Getter


@overload
def deep_serialize(__value: None) -> None: ...


@overload
def deep_serialize(__value: int) -> int: ...


@overload
def deep_serialize(__value: float) -> float: ...


@overload
def deep_serialize(__value: str | date | datetime | Enum) -> str: ...


@overload
def deep_serialize(__value: list | tuple) -> list: ...


@overload
def deep_serialize(__value: dict) -> dict: ...


@overload
def deep_serialize(__value: Iterator) -> Iterator: ...


def deep_serialize(value: Any) -> Any:
    """Deep serialize any data to primitive"""
    if isinstance(value, (float, int, str)) or value is None:
        return value

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, (tuple, list, set)):
        return [deep_serialize(el) for el in value]

    if isinstance(value, dict):
        return {k: deep_serialize(v) for k, v in value.items()}

    if isinstance(value, Iterator):
        return (deep_serialize(item) for item in value)

    try:
        items = dict(value).items()
        return {k: deep_serialize(v) for k, v in items}
    except TypeError:
        raise ValueError(f"Value {str(value)} is not serializable")


def getproperty(element: Any, getter: Getter) -> Any:
    """
    Access a property for an instance or a dict
    Access an index for a list or a tuple
    Either a callback, a string or an int can be given
    """

    if isinstance(getter, str):
        if isinstance(element, dict):
            return element[getter]
        return getattr(element, getter)
    if isinstance(getter, int) and isinstance(element, (tuple, list)):
        return element[getter]
    return getter(element)
