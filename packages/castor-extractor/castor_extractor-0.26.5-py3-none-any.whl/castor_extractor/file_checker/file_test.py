import csv
import os
from collections.abc import Iterator

from .column import ColumnChecker
from .enums import DataType, Issue
from .file import FileCheckerRun, FileTemplate

_TEST_FILE = "file_test_users.csv"
_TEST_FILE_VALID = "file_test_users_valid.csv"


def _content(path: str) -> Iterator[dict]:
    absolute_path = os.path.join(os.path.dirname(__file__), path)
    with open(absolute_path) as csvfile:
        yield from csv.DictReader(csvfile)


def _user_template() -> FileTemplate:
    folder_ids = {"1", "2", "3"}
    return {
        "id": ColumnChecker(is_unique=True),
        "name": ColumnChecker(),
        "gender": ColumnChecker(enum_values={"MALE", "FEMALE"}),
        "birth_date": ColumnChecker(
            data_type=DataType.DATETIME,
            is_mandatory=False,
        ),
        "description": ColumnChecker(is_mandatory=False),
        "siblings_count": ColumnChecker(
            data_type=DataType.INTEGER,
            is_mandatory=False,
        ),
        "height": ColumnChecker(data_type=DataType.FLOAT),
        "folder_id": ColumnChecker(
            data_type=DataType.INTEGER,
            foreign=folder_ids,
        ),
    }


def test__file_checker_run():
    """
    End-to-end test of FileChecker:
    - template (fake users)
    - CSV file
    - results
    """
    content = _content(_TEST_FILE)
    checker = FileCheckerRun(content, _user_template(), _TEST_FILE)

    for _ in checker.valid_rows():
        pass

    assert checker.result.valid_rows == 2
    assert checker.result.total_rows == 9
    assert checker.result.counter[Issue.MISSING_VALUE] == 1
    assert checker.result.counter[Issue.UNAUTHORIZED_VALUE] == 1
    assert checker.result.counter[Issue.WRONG_DATATYPE] == 2
    assert checker.result.counter[Issue.UNKNOWN_REFERENCE] == 1
    assert checker.result.counter[Issue.DUPLICATE_VALUE] == 1
    assert checker.result.counter[Issue.REPEATED_QUOTES] == 1

    content = _content(_TEST_FILE_VALID)
    checker = FileCheckerRun(content, _user_template(), _TEST_FILE_VALID)

    for _ in checker.valid_rows():
        pass

    assert checker.result.is_valid()
