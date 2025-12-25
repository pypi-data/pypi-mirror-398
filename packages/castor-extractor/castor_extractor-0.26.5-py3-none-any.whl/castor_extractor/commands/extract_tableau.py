import logging
from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import tableau  # type: ignore

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    user_group = parser.add_mutually_exclusive_group(required=False)
    user_group.add_argument("-u", "--user", help="Tableau user")
    user_group.add_argument("-n", "--token-name", help="Tableau token name")

    password_group = parser.add_mutually_exclusive_group(required=False)
    password_group.add_argument("-p", "--password", help="Tableau password")
    password_group.add_argument("-t", "--token", help="Tableau token")

    parser.add_argument("-b", "--server-url", help="Tableau server url")
    parser.add_argument("-i", "--site-id", help="Tableau site ID")

    parser.add_argument(
        "--skip-columns",
        dest="skip_columns",
        action="store_true",
        help="Option to avoid extracting Tableau columns, default to False",
    )

    parser.add_argument(
        "--skip-fields",
        dest="skip_fields",
        action="store_true",
        help="Option to avoid extracting Tableau fields, default to False",
    )

    parser.add_argument(
        "--with-pulse",
        dest="with_pulse",
        action="store_true",
        help="Extract Tableau Pulse assets: Metrics and Subscriptions",
    )

    parser.add_argument(
        "--page-size",
        help="Lower the pagination when request exceeds the nodes size limit",
        required=False,
    )

    parser.add_argument(
        "-ie",
        "--ignore-errors",
        action="store_true",
        dest="ignore_errors",
        help="(DEPRECATED) This option no longer has any effect and will be removed in a future version.",
    )
    args = parser.parse_args()
    if args.ignore_errors:
        logger.warning(
            "--ignore-errors is deprecated and has no more effect. It will be removed in a future version."
        )

    parser.add_argument(
        "--ignore-ssl",
        action="store_true",
        dest="ignore_ssl",
        help="Disable SSL verification",
    )

    parser.add_argument("-o", "--output", help="Directory to write to")

    tableau.extract_all(**parse_filled_arguments(parser))
