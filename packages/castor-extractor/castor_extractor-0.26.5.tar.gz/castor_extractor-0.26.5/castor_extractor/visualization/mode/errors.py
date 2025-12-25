from typing import Any
from urllib.error import HTTPError

from requests import Response

from .assets import ModeAnalyticsAsset

RATE_LIMIT_STATUS_CODE = 429


class UnexpectedApiResponseError(Exception):
    """Custom error handling case of unexpected API Response of Mode Analytics"""

    def __init__(self, resource_name: str | None, result: Any):
        error_msg = "Could not extract result from API response."
        error_msg += f"resource_name: {resource_name}"
        error_msg += f"result: {result}"
        super().__init__(error_msg)


class MissingPrerequisiteError(Exception):
    """Custom error handling case of missing asset"""

    def __init__(
        self,
        fetched: ModeAnalyticsAsset,
        missing: ModeAnalyticsAsset,
    ):
        error_msg = f"{missing.name} must be provided to fetch {fetched.name}."
        super().__init__(error_msg)


class RateLimitResponseError(Exception):
    """Custom error handling case of RateLimit of Mode Analytics API"""

    def __init__(self):
        error_msg = "Could not fetch result from API response due to RateLimit"
        super().__init__(error_msg)


def check_errors(response: Response):
    """
    Error check from response.
    If error is 429 (RATE LIMIT) raise custom error RateLimiteResponseError.
    """
    try:
        response.raise_for_status()
    except HTTPError as err:
        if err.code == RATE_LIMIT_STATUS_CODE:
            raise RateLimitResponseError()
        raise err
