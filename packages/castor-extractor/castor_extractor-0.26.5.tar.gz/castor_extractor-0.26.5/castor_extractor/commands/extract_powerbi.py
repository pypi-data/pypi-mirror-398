import logging
from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import powerbi  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()
    auth_group = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument("-t", "--tenant_id", help="PowerBi tenant ID")
    parser.add_argument("-c", "--client_id", help="PowerBi client ID")
    auth_group.add_argument(
        "-s",
        "--secret",
        help="PowerBi password as a string",
    )
    auth_group.add_argument(
        "-cert",
        "--certificate",
        help=(
            "Path to certificate file for authentication. "
            "Accepts: X.509 certificates (.pem, .crt), "
            "PKCS#12 files (.p12, .pfx), or JSON files containing "
            "certificate data or custom authentication secrets."
        ),
    )
    parser.add_argument(
        "-sc",
        "--scopes",
        help="Optional scopes for the Power BI REST API and the Microsoft Graph API",
        nargs="*",
    )
    parser.add_argument("-o", "--output", help="Directory to write to")
    parser.add_argument("-l", "--login_url", help="Login url (Optional)")
    parser.add_argument(
        "-a", "--api_base", help="Power BI REST API base (Optional)"
    )
    parser.add_argument(
        "-g", "--graph_api_base", help="Microsoft Graph API base (Optional)"
    )

    powerbi.extract_all(**parse_filled_arguments(parser))
