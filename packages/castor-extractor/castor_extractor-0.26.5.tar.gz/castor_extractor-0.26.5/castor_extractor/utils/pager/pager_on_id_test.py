from collections.abc import Callable
from uuid import UUID

from .pager_on_id import PagerOnId

ITEMS_WITH_IDS = [
    {"id": "00000000-0000-0000-0000-00000000000" + str(i)} for i in range(1, 10)
]


def _make_callback_with_ids(
    elements: list[dict[str, str]],
) -> Callable[[UUID, int], list[dict[str, str]]]:
    def _callback(max_id: UUID, per: int) -> list[dict[str, str]]:
        """assumes the elements are sorted by id"""
        to_return: list[dict[str, str]] = []
        for element in elements:
            if element["id"] > str(max_id):
                to_return.append(element)
            if len(to_return) >= per:
                return to_return
        return to_return

    return _callback


def test_pageronid__all():
    """relies on ITEMS_WITH_IDS being sorted by id"""
    pager = PagerOnId(_make_callback_with_ids(ITEMS_WITH_IDS))
    # When no argument provided
    assert pager.all() == ITEMS_WITH_IDS
    # When per page is less than the number of ITEMS
    assert pager.all(per_page=1) == ITEMS_WITH_IDS
    # When per page is more than the number of ITEMS
    assert pager.all(per_page=1000) == ITEMS_WITH_IDS


def test_pageronid__iterator__pagination():
    """unit test for PagerOnId#iterator() (pagination)"""
    pager = PagerOnId(_make_callback_with_ids(ITEMS_WITH_IDS))

    def nb_of_pages(per_page: int) -> int:
        return len([page for page in pager.iterator(per_page=per_page)])

    assert nb_of_pages(per_page=50) == 1
    assert nb_of_pages(per_page=1) == len(ITEMS_WITH_IDS)
    assert nb_of_pages(per_page=2) == 5
    assert nb_of_pages(per_page=4) == 3
