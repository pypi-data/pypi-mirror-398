import logging
from collections.abc import Callable
from typing import Any, Union

from requests import HTTPError, Response

logger = logging.getLogger(__name__)

ResponseJson = Union[dict, list[dict]]


class RequestSafeMode:
    """
    RequestSafeMode class to parameterize what should be done if response
    raises due to the status code.

    Attributes:
        self.status_codes: tuple of status codes that will be caught
        self.errors_caught : list of errors caught
    """

    def __init__(
        self,
        max_errors: int | float = 0,
        status_codes: tuple[int, ...] = (),
    ):
        self.max_errors = max_errors
        self.status_codes: list[int] = list(status_codes)
        self.status_codes_caught: list[int] = []

    def catch_response(self, exception: HTTPError, status_code: int):
        if int(status_code) not in self.status_codes:
            raise exception

        self.status_codes_caught.append(int(status_code))

    @property
    def should_raise(self) -> bool:
        return len(self.status_codes_caught) > self.max_errors


def handle_response(
    response: Response,
    safe_mode: RequestSafeMode | None = None,
    handler: Callable | None = None,
) -> Any:
    """
    Util to handle HTTP Response based on the response status code and the
    safe mode used
    """
    safe_mode = safe_mode if safe_mode else RequestSafeMode()
    try:
        response.raise_for_status()
    except HTTPError as e:
        safe_mode.catch_response(e, response.status_code)
        if safe_mode.should_raise:
            raise e
        logger.error(f"Safe mode : skip request with error {e}")
        logger.debug(e, exc_info=True)
        return {}
    if not handler:
        return response.json()
    return handler(response)
