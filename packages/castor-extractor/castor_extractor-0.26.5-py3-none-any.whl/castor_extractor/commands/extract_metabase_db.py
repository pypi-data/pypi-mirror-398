import logging
from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import metabase  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    # mandatory
    parser.add_argument(
        "-H",
        "--host",
        help="Host name where the server is running",
    )
    parser.add_argument("-P", "--port", help="TCP/IP port number")
    parser.add_argument("-d", "--database", help="Database name")
    parser.add_argument("-s", "--schema", help="Schema name")
    parser.add_argument("-u", "--user", help="Username")
    parser.add_argument("-p", "--password", help="Password")
    parser.add_argument(
        "-k",
        "--encryption_secret_key",
        help="Encryption secret key",
    )
    parser.add_argument(
        "--require_ssl",
        action="store_true",
        help="Require SSL",
    )

    parser.add_argument("-o", "--output", help="Directory to write to")

    args = parse_filled_arguments(parser)
    credentials = metabase.MetabaseDbCredentials(**args)

    client = metabase.DbClient(credentials)

    metabase.extract_all(client, **args)
