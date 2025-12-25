from argparse import ArgumentParser

from castor_extractor.utils import parse_filled_arguments  # type: ignore
from castor_extractor.visualization import count  # type: ignore


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "-c",
        "--credentials",
        help="GCP credentials as string",
    )
    parser.add_argument("-o", "--output", help="Directory to write to")
    parser.add_argument(
        "-d",
        "--dataset_id",
        help="dataset id, where count info is stored for the current customer",
    )

    count.extract_all(**parse_filled_arguments(parser))
