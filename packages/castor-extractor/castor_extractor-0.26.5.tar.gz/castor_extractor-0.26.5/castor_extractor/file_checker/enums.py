from enum import Enum


class Issue(Enum):
    """kind of issues we might detect while checking files"""

    MISSING_VALUE = "missing_value"
    UNAUTHORIZED_VALUE = "unauthorized_value"
    WRONG_DATATYPE = "wrong_datatype"
    UNKNOWN_REFERENCE = "unknown_reference"
    DUPLICATE_VALUE = "duplicate_value"
    REPEATED_QUOTES = "repeated_quotes"


class DataType(Enum):
    """data types supported by the file checker"""

    STRING = "string"
    FLOAT = "float"
    INTEGER = "integer"
    DATETIME = "datetime"
    LIST = "list"
