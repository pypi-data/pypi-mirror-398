import logging
from argparse import ArgumentParser

from castor_extractor.knowledge import notion  # type: ignore
from castor_extractor.utils import parse_filled_arguments  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main():
    parser = ArgumentParser()

    parser.add_argument("-t", "--token", help="Notion token")
    parser.add_argument("-o", "--output", help="Directory to write to")

    notion.extract_all(**parse_filled_arguments(parser))
