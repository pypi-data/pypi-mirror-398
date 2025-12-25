from collections.abc import Callable

from .pager import Pager, PagerLogger


def _make_callback(elements: list[int]) -> Callable[[int, int], list[int]]:
    def _callback(page: int, per: int) -> list[int]:
        _start = (page - 1) * per
        _end = _start + per
        return elements[_start:_end]

    return _callback


ITEMS = list(range(10))


def test_Pager__all():
    """unit test for Pager#all()"""
    pager = Pager(_make_callback(ITEMS))
    # When no argument provided
    assert pager.all() == ITEMS
    # When per page is less than the number of ITEMS
    assert pager.all(per_page=1) == ITEMS
    # When per page is more than the number of ITEMS
    assert pager.all(per_page=1000) == ITEMS


def test_Pager__iterator__pagination():
    """unit test for Pager#iterator() (pagination)"""
    pager = Pager(_make_callback(ITEMS))

    def nb_of_pages(per_page: int) -> int:
        return len([page for page in pager.iterator(per_page=per_page)])

    assert nb_of_pages(per_page=50) == 1
    assert nb_of_pages(per_page=1) == 10
    assert nb_of_pages(per_page=2) == 5
    assert nb_of_pages(per_page=4) == 3


def test_Pager__iterator__logging():
    """unit test for Pager#iterator() (pagination)"""

    class Logger(PagerLogger):
        def __init__(self):
            self.pages = []
            self.total = 0

        def on_page(self, page: int, count: int):
            self.pages.append((page, count))

        def on_success(self, page: int, total: int):
            self.total = total

    logger = Logger()
    pager = Pager(_make_callback(ITEMS), logger=logger)

    pager.all(per_page=6)

    assert logger.pages == [(1, 6), (2, 4), (3, 0)]
    assert logger.total == 10
