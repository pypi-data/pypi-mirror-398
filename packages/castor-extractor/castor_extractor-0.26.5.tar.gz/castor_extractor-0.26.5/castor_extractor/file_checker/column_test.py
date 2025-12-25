from .column import ColumnChecker
from .enums import DataType, Issue


def test__column_checker():
    """Test the check() method of ColumnChecker"""

    # test data-type: float
    checker = ColumnChecker(data_type=DataType.FLOAT)
    assert checker.check("foo") == Issue.WRONG_DATATYPE
    assert checker.check("179.5") is None

    # test data-type: int
    checker = ColumnChecker(data_type=DataType.INTEGER)
    assert checker.check("bar") == Issue.WRONG_DATATYPE
    assert checker.check("-56") is None

    # test data-type: datetime
    checker = ColumnChecker(data_type=DataType.DATETIME)
    assert checker.check("calendar") == Issue.WRONG_DATATYPE
    assert checker.check("2021-12-01") is None
    assert checker.check("4/4/99") is None

    # test mandatory
    checker = ColumnChecker(is_mandatory=True)
    assert checker.check("foo") is None
    assert checker.check("") == Issue.MISSING_VALUE
    assert checker.check(None) == Issue.MISSING_VALUE

    # test unicity
    checker = ColumnChecker(is_unique=True)
    assert checker.check("foo") is None
    assert checker.check("bar") is None
    assert checker.check("foo") == Issue.DUPLICATE_VALUE

    # test foreign keys
    ids = {"1", "2", "3", "4", "5"}
    checker = ColumnChecker(foreign=ids)
    assert checker.check("1") is None
    assert checker.check("4") is None
    assert checker.check("99") == Issue.UNKNOWN_REFERENCE

    # test enums
    checker = ColumnChecker(enum_values={"TABLE", "COLUMN"})
    assert checker.check("COLUMN") is None
    assert checker.check("TABLE") is None
    assert checker.check("VIEW") == Issue.UNAUTHORIZED_VALUE

    # test data-type: list
    checker = ColumnChecker(data_type=DataType.LIST, is_mandatory=True)
    assert checker.check("") == Issue.MISSING_VALUE
    assert checker.check(None) == Issue.MISSING_VALUE
    assert checker.check("['foo', 'bar']") is None
    assert checker.check('["foo", "bar"]') is None
