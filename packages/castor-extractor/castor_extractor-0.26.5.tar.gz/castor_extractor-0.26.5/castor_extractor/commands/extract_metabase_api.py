import logging
from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import metabase  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-b", "--base-url", help="Metabase base url")
    parser.add_argument("-u", "--user", help="Metabase username")
    parser.add_argument("-p", "--password", help="Metabase password")

    parser.add_argument("-o", "--output", help="Directory to write to")

    args = parse_filled_arguments(parser)

    credentials = metabase.MetabaseApiCredentials(**args)
    client = metabase.ApiClient(credentials)

    metabase.extract_all(client, **args)
