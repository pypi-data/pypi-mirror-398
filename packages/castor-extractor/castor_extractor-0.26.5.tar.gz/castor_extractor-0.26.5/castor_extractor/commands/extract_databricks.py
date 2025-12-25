import logging
from argparse import ArgumentParser

from castor_extractor.warehouse import databricks  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-H", "--host", help="Databricks host")
    parser.add_argument(
        "--catalog-allowed",
        nargs="*",
        help="List of databricks catalogs that should be extracted",
    )
    parser.add_argument(
        "--catalog-blocked",
        nargs="*",
        help="List of databricks catalogs that should not be extracted",
    )
    parser.add_argument("-t", "--token", help="Databricks access token")
    parser.add_argument(
        "-p", "--http-path", dest="http_path", help="Databricks http path"
    )
    parser.add_argument("-o", "--output", help="Directory to write to")
    parser.add_argument(
        "--skip-existing",
        dest="skip_existing",
        action="store_true",
        help="Skips files already extracted instead of replacing them",
    )
    parser.set_defaults(skip_existing=False)

    args = parser.parse_args()

    databricks.extract_all(
        db_allowed=args.catalog_allowed,
        db_blocked=args.catalog_blocked,
        host=args.host,
        output_directory=args.output,
        token=args.token,
        http_path=args.http_path,
        skip_existing=args.skip_existing,
    )
