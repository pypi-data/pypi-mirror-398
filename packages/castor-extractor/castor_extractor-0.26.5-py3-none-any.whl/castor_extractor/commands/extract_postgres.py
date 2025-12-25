import logging
from argparse import ArgumentParser

from castor_extractor.warehouse import postgres  # type:ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-H", "--host", help="Postgres Host")
    parser.add_argument("-P", "--port", help="Postgres Port")
    parser.add_argument("-d", "--database", help="Postgres Database")
    parser.add_argument("-u", "--user", help="Postgres User")
    parser.add_argument("-p", "--password", help="Postgres Password")

    parser.add_argument("-o", "--output", help="Directory to write to")

    parser.add_argument(
        "--skip-existing",
        dest="skip_existing",
        action="store_true",
        help="Skips files already extracted instead of replacing them",
    )
    parser.set_defaults(skip_existing=False)

    args = parser.parse_args()

    postgres.extract_all(
        host=args.host,
        database=args.database,
        port=args.port,
        user=args.user,
        password=args.password,
        output_directory=args.output,
        skip_existing=args.skip_existing,
    )
