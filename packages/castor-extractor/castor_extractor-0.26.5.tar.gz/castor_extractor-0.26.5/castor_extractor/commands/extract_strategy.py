import logging
from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import strategy  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-u", "--username", help="Strategy username")
    parser.add_argument("-p", "--password", help="Strategy password")
    parser.add_argument("-b", "--base-url", help="Strategy instance URL")
    parser.add_argument("-o", "--output", help="Directory to write to")

    parser.add_argument(
        "-i",
        "--project-ids",
        nargs="*",
        help="Optional list of project IDs",
        default=None,
    )

    strategy.extract_all(**parse_filled_arguments(parser))
