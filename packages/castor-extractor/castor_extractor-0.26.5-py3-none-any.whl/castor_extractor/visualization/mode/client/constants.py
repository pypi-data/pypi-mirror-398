from requests.exceptions import (
    ConnectionError as RequestConnectionError,
    Timeout as RequestTimeout,
)

from ....utils import RetryStrategy
from ..errors import RateLimitResponseError

RETRY_EXCEPTIONS = (
    RateLimitResponseError,
    ConnectionError,
    RequestConnectionError,
    RequestTimeout,
)
RETRY_COUNT = 2
RETRY_BASE_MS = 10_000
RETRY_JITTER_MS = 1_000
RETRY_STRATEGY = RetryStrategy.LINEAR


CLIENT_NAME = "ModeAnalytics/API"
