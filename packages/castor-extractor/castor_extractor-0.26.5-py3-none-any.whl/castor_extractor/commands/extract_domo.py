import logging
from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import domo  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    # mandatory
    parser.add_argument(
        "-b",
        "--base-url",
        help="Host name where the server is running",
    )
    parser.add_argument(
        "-a",
        "--api-token",
        help="Token to connect to Domo",
    )
    parser.add_argument(
        "-d",
        "--developer-token",
        help="Developer token to use private API",
    )
    parser.add_argument(
        "-c",
        "--client-id",
        help="Client id of the Domo account",
    )
    parser.add_argument(
        "-C",
        "--cloud-id",
        help="Cloud id is the external warehouse id within Domo",
    )

    parser.add_argument("-o", "--output", help="Directory to write to")

    domo.extract_all(**parse_filled_arguments(parser))
