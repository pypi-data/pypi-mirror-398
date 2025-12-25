import logging
from abc import abstractmethod
from collections.abc import Callable, Iterator
from enum import Enum
from functools import partial
from time import sleep

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class FetchNextPageBy(Enum):
    """
    Enum to pick which APIClient._call() argument we want
    to use for calling the next page in the pagination.
    Supported arguments are :
    - params (PAYLOAD)
    - endpoint (URL)
    """

    PAYLOAD = "pagination_params"
    URL = "endpoint"


class PaginationModel(BaseModel):
    """
    Base abstract class defining a pagination model

    By implementing the 3 abstract methods below, enables
    to fetch all elements of a Paginated API by using the
    `fetch_all_pages` method
    """

    fetch_by: FetchNextPageBy = FetchNextPageBy.PAYLOAD
    current_page_payload: dict | None = None

    @abstractmethod
    def is_last(self) -> bool:
        """Stopping condition for the pagination"""
        pass

    @abstractmethod
    def next_page_payload(self) -> dict | str | None:
        """Payload enabling to generate the request for the next page"""
        pass

    @abstractmethod
    def page_results(self) -> list:
        """List of results of the current page"""
        pass

    def next_page_parameters(self) -> dict:
        return {self.fetch_by.value: self.next_page_payload()}


def fetch_all_pages(
    request: Callable,
    pagination_model: type[PaginationModel],
    rate_limit: float | None = None,
) -> Iterator:
    """
    Method to return all results of a Paginated API based on the
    pagination model and the first request call
    """
    page_number = 1
    response_payload = request()

    paginated_response = pagination_model(**response_payload)

    while not paginated_response.is_last():
        logger.debug(f"Fetching page number {page_number}")
        yield from paginated_response.page_results()
        next_page_parameters = paginated_response.next_page_parameters()
        request_with_pagination = partial(request, **next_page_parameters)
        if rate_limit:
            sleep(rate_limit)
        paginated_response = pagination_model(
            current_page_payload=next_page_parameters,
            **request_with_pagination(),
        )
        page_number += 1

    # send last page's results
    logger.debug(f"Fetching page number {page_number}")
    yield from paginated_response.page_results()
