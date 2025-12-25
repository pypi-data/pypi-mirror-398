import logging
from collections.abc import Iterator
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def batch_of_length(
    elements: list[T],
    batch_size: int,
) -> Iterator[list[T]]:
    """
    Split the given elements into smaller chunks
    """
    assert batch_size > 1, "batch size must be greater or equal to 1"
    element_count = len(elements)
    for index in range(0, element_count, batch_size):
        logger.info(f"Processing {index}/{element_count}")
        yield elements[index : min((index + batch_size), element_count)]
