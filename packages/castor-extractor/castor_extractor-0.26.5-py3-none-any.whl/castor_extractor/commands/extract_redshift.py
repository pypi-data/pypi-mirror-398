import logging
from argparse import ArgumentParser

from castor_extractor.warehouse import redshift  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-H", "--host", help="Redshift Host")
    parser.add_argument("-P", "--port", help="Redshift Port")
    parser.add_argument("-d", "--database", help="Redshift Database")
    parser.add_argument("-u", "--user", help="Redshift User")
    parser.add_argument("-p", "--password", help="Redshift Password")

    parser.add_argument("-o", "--output", help="Directory to write to")

    parser.add_argument(
        "--skip-existing",
        dest="skip_existing",
        action="store_true",
        help="Skips files already extracted instead of replacing them",
    )
    parser.add_argument(
        "--serverless",
        action="store_true",
        help="Enables extraction for Redshift Serverless",
    )
    parser.set_defaults(skip_existing=False)

    args = parser.parse_args()

    redshift.extract_all(
        host=args.host,
        database=args.database,
        port=args.port,
        user=args.user,
        password=args.password,
        output_directory=args.output,
        serverless=args.serverless,
        skip_existing=args.skip_existing,
    )
