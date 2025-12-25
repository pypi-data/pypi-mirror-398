import logging
import os
from argparse import ArgumentParser

from castor_extractor import file_checker  # type: ignore
from castor_extractor.utils import (  # type: ignore
    LocalStorage,  # type: ignore
    explode,
    search_files,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

WarehouseTemplate = file_checker.GenericWarehouseFileTemplate

Ids = set[str]
_ID_KEY = "id"


def process(directory: str, verbose: bool):
    """
    Checks all files necessary to push Generic Warehouse
    """
    storage = LocalStorage(directory=directory, with_timestamp=False)

    def _find(name: str) -> str:
        files = search_files(
            directory,
            filter_endswith=name,
            filter_extensions={"csv"},
        )
        assert files, f"Could not find files ending with {name}.csv"

        most_recent = max(files, key=os.path.getctime)
        _, filename, _ = explode(most_recent)
        return filename

    def _check(
        name: str,
        template: file_checker.FileTemplate,
        *,
        with_ids: bool = True,
    ) -> Ids:
        filename = _find(name)
        content = storage.get(filename)
        checker = file_checker.FileCheckerRun(
            content,
            template,
            filename,
            verbose,
        )
        checker.validate()
        if not with_ids:
            return set()
        return checker.occurrences(_ID_KEY)

    database_template = WarehouseTemplate.database()
    database_ids = _check("database", database_template)

    schema_template = WarehouseTemplate.schema(database_ids)
    schema_ids = _check("schema", schema_template)

    table_template = WarehouseTemplate.table(schema_ids)
    table_ids = _check("table", table_template)

    column_template = WarehouseTemplate.column(table_ids)
    _check("column", column_template, with_ids=False)

    user_template = WarehouseTemplate.user()
    user_ids = _check("user", user_template)

    view_ddl_template = WarehouseTemplate.view_ddl()
    _check("view_ddl", view_ddl_template, with_ids=False)

    query_template = WarehouseTemplate.query(database_ids, user_ids)
    _check("query", query_template, with_ids=False)


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--directory",
        help="Directory containing the files to be checked",
    )
    parser.add_argument(
        "--verbose",
        dest="display_issues",
        action="store_true",
        help="Show detailed logs",
    )
    args = parser.parse_args()
    process(args.directory, args.display_issues)
