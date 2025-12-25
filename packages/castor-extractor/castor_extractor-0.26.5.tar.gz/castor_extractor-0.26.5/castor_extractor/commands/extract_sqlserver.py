import logging
from argparse import ArgumentParser

from castor_extractor.warehouse import sqlserver  # type:ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-H", "--host", help="MSSQL Host")
    parser.add_argument("-P", "--port", help="MSSQL Port")
    parser.add_argument("-u", "--user", help="MSSQL User")
    parser.add_argument("-p", "--password", help="MSSQL Password")

    parser.add_argument(
        "-s",
        "--skip-queries",
        dest="skip_queries",
        action="store_true",
        help="Skip the extraction of SQL queries",
    )

    parser.add_argument("-o", "--output", help="Directory to write to")

    parser.add_argument(
        "--skip-existing",
        dest="skip_existing",
        action="store_true",
        help="Skips files already extracted instead of replacing them",
    )
    parser.add_argument(
        "--db-allowed",
        nargs="*",
        help="List of databases that should be extracted",
    )
    parser.add_argument(
        "--db-blocked",
        nargs="*",
        help="List of databases that should not be extracted",
    )
    parser.set_defaults(skip_existing=False)

    args = parser.parse_args()

    sqlserver.extract_all(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        output_directory=args.output,
        skip_existing=args.skip_existing,
        db_allowed=args.db_allowed,
        db_blocked=args.db_blocked,
    )
