import logging
from collections.abc import Iterable, Iterator

from .column import ColumnChecker
from .enums import Issue

logger = logging.getLogger(__name__)

_SEPARATOR = f"{30 * '-'}\n"

FileTemplate = dict[str, ColumnChecker]  # column_name, column_checker
IssueCounter = dict[Issue, int]  # occurrences per type of issue


class FileCheckerResults:
    """
    Results produced by FileCheckerRun.
    Gives the number of valid rows and the number of issues encountered.
    """

    def __init__(self):
        self.total_rows: int = 0
        self.valid_rows: int = 0
        self.counter: IssueCounter = {issue: 0 for issue in Issue}
        self.indices: set[int] = set()

    def summary(self) -> str:
        """
        builds message containing the main information:
        - total rows in the file
        - status (valid / ERROR)
        - number of invalid rows
        """
        invalid = self.total_rows - self.valid_rows
        msg = f"{self.total_rows} rows -- "
        msg += "valid" if invalid == 0 else f"ERROR ({invalid} invalid rows)"
        return msg

    def invalid_rows(self) -> str:
        """
        builds message containing indices of invalid rows
        """
        rows = list(map(str, sorted([index for index in self.indices])))
        if len(rows) > 10:
            rows = [*rows[:5], "...", *rows[-5:]]
        return "Invalid rows: " + ", ".join([f"#{row}" for row in rows])

    def issues(self) -> str:
        """
        builds message containing information about encountered issues
        """
        issues = [
            f"| {issue.name}: {count}"
            for issue, count in self.counter.items()
            if count > 0
        ]
        return "\n".join(issues)

    def is_valid(self) -> bool:
        return self.valid_rows == self.total_rows


class FileCheckerRun:
    """
    Validates the given file content, using template.
    """

    def __init__(
        self,
        content: Iterable[dict],
        template: FileTemplate,
        file_name: str,
        verbose: bool = False,
    ):
        self.content = content
        self.template = template
        self.file_name = file_name
        self.verbose = verbose
        self.result = FileCheckerResults()
        self.logger = logging.getLogger(__name__)

    def _record_issue(self, issue: Issue, index: int):
        self.result.counter[issue] += 1
        self.result.indices.add(index + 1)  # easier to understand for end user

    @staticmethod
    def _issue_description(
        name: str,
        checker: ColumnChecker,
        issue: Issue,
    ) -> str:
        """
        Build message describing issue:
        - name of the column
        - name of the issue
        - additional info for the end user (what was expected)
        """
        msg = f"[{name}] - {issue.name}"
        if issue == Issue.WRONG_DATATYPE:
            msg += f" - Expecting {checker.data_type}"
        if issue == Issue.UNAUTHORIZED_VALUE:
            msg += f" - Expecting one of {checker.enum_values}"
        return msg + "\n"

    def _log(self, index: int, row: dict, issue_log: str) -> None:
        """
        Show the given row and its issues.
        Example:
        ```
        Issues detected on Row #3
          id                   3
          name                 christina
          gender               woman
          birth_date           1956-04-01
          description
          height               1.57
          folder_id            9999
        ------------------------------
        [gender]    - UNAUTHORIZED_VALUE - Expecting one of {'FEMALE', 'MALE'}
        [folder_id] - UNKNOWN_REFERENCE
        ------------------------------
        ```
        """
        if not self.verbose:
            return
        header = f"Issues detected on Row #{index + 1}\n"
        for k, v in row.items():
            header += f"{str(k):<20} {str(v):<100}\n"
        self.logger.info(header + _SEPARATOR + issue_log + _SEPARATOR)

    def occurrences(self, name: str) -> set[str]:
        """
        Return values of the given column, provided:
        - the column exists in the template
        - the column is set to UNIQUE (which means occurrences are recorded)
        """
        assert name in self.template, f"Unknown column in template: {name}"
        checker = self.template[name]
        msg = "Cannot return occurrences of non-unique column"
        assert checker.is_unique, msg
        return checker.occurrences

    def summary(self):
        """
        Show general information after running checks:
        - file name & validation status (OK / ERROR)
        - number of rows (invalid/total)
        - summary of the issues: rows index + count per issue type
        """
        msg = f"{self.file_name.upper()} -- {self.result.summary()}\n"
        if not self.result.is_valid():
            msg += self.result.invalid_rows() + "\n"
            msg += self.result.issues() + "\n"
        logger.info(msg + "\n")

    def validate(self) -> None:
        """Validate the whole file without using the content"""
        for _ in self.valid_rows():
            pass

    def valid_rows(self) -> Iterator[dict]:
        """
        Reads the file content and yields only valid rows.
        - Invalid rows are ignored
        - Show detailed issues and the associated row content if verbose

        After reading the whole content, show summary.

        Also, feeds the FileCheckerResults:
        - number of invalid rows
        - number of issues per type

        Example of usage:
        ```
        checker = FileCheckerRun(content, template)
        for valid in checker.valid_rows():
            process(valid)
        if not checker.is_valid():
            raise AssertionError("File cannot be processed, issues detected")
        ```
        """
        for index, row in enumerate(self.content):
            self.result.total_rows += 1
            has_issue = False
            issue_log = ""
            for name, template in self.template.items():
                value = row.get(name)
                issue = template.check(value)
                if not issue:
                    continue
                has_issue = True
                self._record_issue(issue, index)
                issue_log += self._issue_description(name, template, issue)
            if has_issue:
                self._log(index, row, issue_log)
                continue  # don't return the row
            self.result.valid_rows += 1
            yield row
        self.summary()
