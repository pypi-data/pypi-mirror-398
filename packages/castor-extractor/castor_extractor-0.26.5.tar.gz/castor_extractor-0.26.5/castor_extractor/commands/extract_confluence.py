import logging
from argparse import ArgumentParser

from castor_extractor.knowledge import confluence  # type: ignore
from castor_extractor.utils import parse_filled_arguments  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-a", "--account_id", help="Confluence account id")
    parser.add_argument("-b", "--base_url", help="Confluence account base url")
    parser.add_argument("-o", "--output", help="Directory to write to")
    parser.add_argument("-t", "--token", help="Confluence API token")
    parser.add_argument("-u", "--username", help="Confluence username")

    parser.add_argument(
        "--include-archived-spaces",
        action="store_true",
        default=False,
        help="Include pages from archived spaces (Optional)",
    )
    parser.add_argument(
        "--include-personal-spaces",
        action="store_true",
        default=False,
        help="Include pages from personal spaces (Optional)",
    )
    parser.add_argument(
        "--space-ids-allowed",
        type=str,
        nargs="+",
        help=(
            "List of Confluence space IDs allowed for extraction (Optional). "
            "Only pages from these Spaces will be extracted. "
            "This overrides any other filtering (archived, personal, etc.)"
        ),
    )
    parser.add_argument(
        "--space-ids-blocked",
        type=str,
        nargs="+",
        help="List of Confluence space IDs to exclude fom the extraction (Optional)",
    )

    confluence.extract_all(**parse_filled_arguments(parser))
