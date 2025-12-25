from abc import abstractmethod
from collections.abc import Callable, Iterator, Sequence
from enum import Enum
from itertools import chain
from typing import (
    Generic,
    TypeVar,
)

DEFAULT_PER_PAGE = 100

T = TypeVar("T")


class PagerLogger:
    def on_page(self, page: int, count: int):
        pass

    def on_success(self, page: int, total: int):
        pass


class PagerStopStrategy(Enum):
    """Strategy for stopping the pager"""

    EMPTY_PAGE = "EMPTY_PAGE"
    LESS_RESULTS_THAN_ASKED = "LESS_RESULTS_THAN_ASKED"


class AbstractPager(Generic[T]):
    def all(self, per_page: int = DEFAULT_PER_PAGE) -> list[T]:
        """Returns all data provided by the callback as a list"""
        return list(chain.from_iterable(self.iterator(per_page=per_page)))

    @abstractmethod
    def iterator(self, per_page: int) -> Iterator[Sequence[T]]:
        pass

    @staticmethod
    def should_stop(nb_results: int, per_page: int, stop_on_empty_page: bool):
        is_empty = nb_results == 0
        is_partial_page = nb_results < per_page
        should_stop = is_empty if stop_on_empty_page else is_partial_page
        return should_stop


class Pager(AbstractPager[T]):
    def __init__(
        self,
        callback: Callable[[int, int], Sequence[T]],
        *,
        logger: PagerLogger | None = None,
        start_page: int = 1,
        stop_strategy: PagerStopStrategy = PagerStopStrategy.EMPTY_PAGE,
    ):
        self._callback = callback
        self._logger = logger or PagerLogger()
        self._start_page = start_page
        self._stop_strategy = stop_strategy

    def iterator(
        self,
        per_page: int = DEFAULT_PER_PAGE,
    ) -> Iterator[Sequence[T]]:
        """Yields data provided by the callback as a list page by page"""
        page = self._start_page
        total_results = 0

        stop_on_empty_page = self._stop_strategy == PagerStopStrategy.EMPTY_PAGE

        while True:
            results = self._callback(page, per_page)
            nb_results = len(results)
            total_results += nb_results

            self._logger.on_page(page, nb_results)
            if results:
                yield results

            stop = self.should_stop(nb_results, per_page, stop_on_empty_page)

            if stop:
                break

            page += 1

        self._logger.on_success(page, total_results)
