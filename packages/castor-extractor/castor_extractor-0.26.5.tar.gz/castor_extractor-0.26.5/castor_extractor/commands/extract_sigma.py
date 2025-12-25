import logging
from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import sigma  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-H", "--host", help="Sigma host")
    parser.add_argument("-c", "--client-id", help="Sigma client ID")
    parser.add_argument("-a", "--api-token", help="Generated API key")
    parser.add_argument("-o", "--output", help="Directory to write to")

    sigma.extract_all(**parse_filled_arguments(parser))
