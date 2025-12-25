import logging
import math

logger = logging.getLogger(__name__)


class SmartPagination:
    """
    Pagination helper that dynamically reduces page size when encountering
    slow or timing-out API responses.

    It supports progressive fallback
    (e.g., 200 → 100 → 10 → 1) and resets back to the initial page size once
    the problematic segment is passed.
    """

    def __init__(self, initial_page_size: int) -> None:
        self.initial_page_size = initial_page_size
        self._reduced_page_size = None
        self._counter = None
        self._slow_mode = False

    @property
    def page_size(self):
        return self._reduced_page_size or self.initial_page_size

    def reduce_page_size(self):
        new_page_size = math.ceil(self.page_size / 10)
        logger.info(
            f"Page size reduced from {self.page_size} to {new_page_size}"
        )
        self._reduced_page_size = new_page_size
        if not self._slow_mode:
            # we just entered a problematic batch
            # start the countdown
            self._counter = 0
            self._slow_mode = True

    def reset(self):
        """
        Manual reset is useful after skipping a faulty row: we want to get back
        at full speed, under the assumption that the timeouts are behind us
        """
        logger.info(f"Resetting initial page size: {self.initial_page_size}")
        self._reduced_page_size = None
        self._counter = None
        self._slow_mode = False

    def next(self):
        """
        Advance the counter when operating in slow mode.
        Once the problematic segment has been fully traversed,
        automatically restore the initial pagination strategy to resume
        efficient extraction.
        """
        if not self._slow_mode:
            return
        self._counter += self._reduced_page_size
        if self._counter >= self.initial_page_size:
            self.reset()
