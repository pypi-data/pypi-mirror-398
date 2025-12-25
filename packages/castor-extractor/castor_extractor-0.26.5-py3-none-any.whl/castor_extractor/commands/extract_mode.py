import logging
from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import mode  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-H", "--host", help="Mode Analytics host")
    parser.add_argument("-w", "--workspace", help="Mode Analytics workspace")
    parser.add_argument(
        "-t",
        "--token",
        help="The Token value from the API token",
    )
    parser.add_argument(
        "-s",
        "--secret",
        help="The Password value from the API token",
    )

    parser.add_argument("-o", "--output", help="Directory to write to")

    mode.extract_all(**parse_filled_arguments(parser))
