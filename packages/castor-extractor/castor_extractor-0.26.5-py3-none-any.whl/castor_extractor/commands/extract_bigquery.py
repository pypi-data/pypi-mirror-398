from argparse import ArgumentParser

from castor_extractor.warehouse import bigquery  # type: ignore


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "-c",
        "--credentials",
        help="File path to google credentials",
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
        help="List of gcp projects that should be extracted",
    )
    parser.add_argument(
        "--db-blocked",
        nargs="*",
        help="List of gcp projects that should not be extracted",
    )
    parser.add_argument(
        "--safe-mode",
        "-s",
        help="bigquery safe mode",
        action="store_true",
    )

    parser.set_defaults(skip_existing=False)

    args = parser.parse_args()

    bigquery.extract_all(
        credentials=args.credentials,
        output_directory=args.output,
        skip_existing=args.skip_existing,
        db_allowed=args.db_allowed,
        db_blocked=args.db_blocked,
        safe_mode=args.safe_mode,
    )
