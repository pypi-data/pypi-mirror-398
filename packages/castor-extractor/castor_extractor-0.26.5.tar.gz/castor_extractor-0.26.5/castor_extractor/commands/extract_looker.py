from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import looker  # type: ignore


def main():
    parser = ArgumentParser()
    parser.add_argument("-b", "--base-url", help="Looker base url")
    parser.add_argument("-c", "--client-id", help="Looker client id")
    parser.add_argument("-s", "--client-secret", help="Looker client secret")
    parser.add_argument("-o", "--output", help="Directory to write to")
    parser.add_argument("-t", "--timeout", type=int, help="Timeout in seconds")
    parser.add_argument(
        "--thread-pool-size",
        type=int,
        help="Thread pool size, if searching per folder",
    )
    parser.add_argument(
        "--safe-mode",
        "-S",
        help="Looker safe mode",
        action="store_true",
    )
    parser.add_argument(
        "--log-to-stdout",
        help="Send all log outputs to stdout instead of stderr",
        action="store_true",
    )

    parser.add_argument(
        "--search-per-folder",
        help="Fetches Looks and Dashboards per folder",
        action="store_true",
    )

    looker.extract_all(**parse_filled_arguments(parser))
