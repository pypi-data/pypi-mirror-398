from argparse import ArgumentParser


def parse_filled_arguments(parser: ArgumentParser) -> dict:
    """Parse arguments and remove all those with None values"""
    parsed_arguments = vars(parser.parse_args())
    return {k: v for k, v in parsed_arguments.items() if v is not None}
