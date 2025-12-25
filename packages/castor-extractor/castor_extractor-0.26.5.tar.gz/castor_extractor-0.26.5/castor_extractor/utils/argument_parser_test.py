from argparse import Namespace

from .argument_parser import parse_filled_arguments


class MockArgumentParser:
    def __init__(self):
        self.attributes = {}

    def add_argument(self, name, value):
        self.attributes[name] = value

    def parse_args(self) -> Namespace:
        return Namespace(**self.attributes)


def test_parse_filled_arguments():
    parser = MockArgumentParser()
    parser.add_argument("filled", "value")
    parser.add_argument("unfilled", None)
    parser.add_argument("empty_str", "")

    expected = {"filled": "value", "empty_str": ""}
    assert parse_filled_arguments(parser) == expected
