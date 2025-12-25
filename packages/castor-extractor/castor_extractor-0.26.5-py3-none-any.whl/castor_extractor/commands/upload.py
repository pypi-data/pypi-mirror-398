import logging
from argparse import ArgumentParser

from castor_extractor.uploader import (  # type: ignore
    FileType,
    Zone,
    upload_any,
)
from castor_extractor.utils import parse_filled_arguments  # type: ignore

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def _args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "-k",
        "--token",
        help="API token provided by CastorDoc",
    )
    parser.add_argument(
        "-s",
        "--source_id",
        help="source id provided by CastorDoc",
    )
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-f", "--file_path", help="path to file to upload")
    group.add_argument(
        "-d",
        "--directory_path",
        help="""directory containing the files to upload.
                WARNING: it will upload all the files included
                in the given repository.""",
    )
    supported_file_type = [ft.value for ft in FileType]
    parser.add_argument(
        "-t",
        "--file_type",
        help="type of file to upload, currently supported are {}".format(
            supported_file_type,
        ),
        choices=supported_file_type,
    )
    supported_zones = [zone.value for zone in Zone]
    parser.add_argument(
        "-z",
        "--zone",
        help="geographic zone to upload, currently supported are {}, defaults to EU".format(
            supported_zones,
        ),
        choices=supported_zones,
    )
    return parser


def main():
    parser = _args()
    upload_any(**parse_filled_arguments(parser))
