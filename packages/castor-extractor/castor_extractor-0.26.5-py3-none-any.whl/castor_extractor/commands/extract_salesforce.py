import logging
from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.warehouse import salesforce  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-u", "--username", help="Salesforce username")
    parser.add_argument("-p", "--password", help="Salesforce password")
    parser.add_argument("-c", "--client-id", help="Salesforce client id")
    parser.add_argument(
        "-s", "--client-secret", help="Salesforce client secret"
    )
    parser.add_argument(
        "-t", "--security-token", help="Salesforce security token"
    )
    parser.add_argument("-b", "--base-url", help="Salesforce instance URL")
    parser.add_argument("-o", "--output", help="Directory to write to")

    parser.add_argument(
        "--skip-existing",
        dest="skip_existing",
        action="store_true",
        help="Skips files already extracted instead of replacing them",
    )
    parser.set_defaults(skip_existing=False)

    args = parse_filled_arguments(parser)
    salesforce.extract_all(output_directory=args.get("output"), **args)
