from collections.abc import Callable, Iterator, Sequence
from typing import Protocol, TypeVar
from uuid import UUID

from .pager import DEFAULT_PER_PAGE, AbstractPager, PagerStopStrategy

_DEFAULT_MIN_UUID = UUID("00000000-0000-0000-0000-000000000000")


class IndexableObject(Protocol):
    def __getitem__(self, key: str) -> UUID: ...


Indexable = TypeVar("Indexable", bound=IndexableObject)


class PagerOnIdLogger:
    def on_iteration(self, max_id: UUID, count: int):
        pass

    def on_success(self, total: int):
        pass


class PagerOnId(AbstractPager[Indexable]):
    def __init__(
        self,
        callback: Callable[[UUID, int], Sequence[Indexable]],
        *,
        logger: PagerOnIdLogger | None = None,
        stop_strategy: PagerStopStrategy = PagerStopStrategy.EMPTY_PAGE,
    ):
        self._callback = callback
        self._logger = logger or PagerOnIdLogger()
        self._stop_strategy = stop_strategy

    @staticmethod
    def _max_id(items: Sequence[Indexable]) -> UUID:
        return max(item["id"] for item in items)

    def iterator(
        self,
        per_page: int = DEFAULT_PER_PAGE,
    ) -> Iterator[Sequence[Indexable]]:
        """Yields data provided by the callback as a list using the greatest UUID as a reference point"""
        greater_than_id = _DEFAULT_MIN_UUID
        stop_on_empty_page = self._stop_strategy == PagerStopStrategy.EMPTY_PAGE

        total_results = 0

        while True:
            results = self._callback(greater_than_id, per_page)
            nb_results = len(results)
            total_results += nb_results

            if results:
                greater_than_id = self._max_id(results)
                self._logger.on_iteration(greater_than_id, nb_results)
                yield results

            stop = self.should_stop(nb_results, per_page, stop_on_empty_page)

            if stop:
                break
        self._logger.on_success(total_results)
