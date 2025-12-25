from typing import Any, Union, cast

Field = Union[str, dict[str, Any]]
Fields = Union[Field, tuple[Field, ...]]


def format_fields(fields: Fields) -> str:
    """format field for looker api"""

    if isinstance(fields, str):
        return fields

    if isinstance(fields, dict):
        formatted = {
            k: format_fields(cast(Fields, v)) for k, v in fields.items()
        }
        return ", ".join(f"{k}({v})" for k, v in formatted.items())

    if isinstance(fields, tuple):
        return ", ".join(format_fields(f) for f in fields)

    raise ValueError(f"Expected tuple, dict or string, got: {fields}")
