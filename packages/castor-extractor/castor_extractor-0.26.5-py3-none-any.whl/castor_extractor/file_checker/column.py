from collections.abc import Callable

from dateutil.parser import parse

from ..utils import string_to_tuple
from .enums import DataType, Issue

_CONVERTERS: dict[DataType, Callable] = {
    DataType.DATETIME: parse,
    DataType.FLOAT: float,
    DataType.INTEGER: int,
    DataType.STRING: str,
    DataType.LIST: string_to_tuple,
}


class ColumnChecker:
    """
    Provides rules and methods to validate column content (FileChecker).

    Handles the necessary context for validation:
    - Set of occurrences (to check unicity)
    - Set of foreign values (to check FK)
    """

    def __init__(
        self,
        *,
        data_type: DataType = DataType.STRING,
        is_mandatory: bool = True,
        is_unique: bool = False,
        foreign: set[str] | None = None,
        enum_values: set[str] | None = None,
    ):
        self.data_type = data_type
        self.is_mandatory = is_mandatory
        self.is_unique = is_unique
        self.occurrences: set[str] = set()
        self.foreign = foreign
        self.enum_values = enum_values

    def _check_data_type(self, value: str) -> bool:
        """
        Check that the given value can be converted as expected
        """
        convert = _CONVERTERS[self.data_type]
        try:
            convert(value)
        except ValueError:
            return False
        return True

    def _check_enum(self, value: str) -> bool:
        """
        Check that the given value can be converted to ENUM
        Example: gender = {MALE|FEMALE}
        """
        if self.enum_values and value not in self.enum_values:
            return False
        return True

    def _check_unicity(self, value: str) -> bool:
        """
        Check that the given value is unique.
        Add the value to the list of occurrences.
        """
        if not self.is_unique:
            return True
        if value in self.occurrences:
            return False
        self.occurrences.add(value)
        return True

    def _check_foreign(self, value: str) -> bool:
        """
        Check that the given value refers to an existing value
        """
        if not self.foreign:
            return True
        return value in self.foreign

    def check(self, value: str | None) -> Issue | None:
        """
        Do all checks to validate that the given value respect the column rules.
        Return an issue if something's wrong.
        Issues are mutually exclusives => no no need to return a list.
        """
        if value is None or value == "":
            if self.is_mandatory:
                return Issue.MISSING_VALUE
            return None

        if value.strip('"') != value:
            return Issue.REPEATED_QUOTES

        if not self._check_enum(value):
            return Issue.UNAUTHORIZED_VALUE
        if not self._check_data_type(value):
            return Issue.WRONG_DATATYPE
        if not self._check_unicity(value):
            return Issue.DUPLICATE_VALUE
        if not self._check_foreign(value):
            return Issue.UNKNOWN_REFERENCE
        return None
