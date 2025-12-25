from collections.abc import Callable, Iterator
from functools import partial

from ....utils import (
    APIClient,
    BasicAuth,
    fetch_all_pages,
)
from ..assets import SodaAsset
from .credentials import SodaCredentials
from .endpoints import SodaEndpointFactory
from .pagination import SodaCloudPagination

_REQUESTS_PER_MINUTE = 10
_SECONDS_PER_MINUTE = 60
_RATE_LIMIT_MS = (_SECONDS_PER_MINUTE // _REQUESTS_PER_MINUTE) + 1
_CLOUD_PAGE_SIZE = 100

HEADERS = {"Content-Type": "application/json"}


class SodaClient(APIClient):
    def __init__(self, credentials: SodaCredentials):
        cloud_auth = BasicAuth(
            username=credentials.api_key, password=credentials.secret
        )
        super().__init__(
            host=credentials.host, auth=cloud_auth, headers=HEADERS
        )

    @property
    def _base_request(self) -> Callable:
        return partial(self._get, params={"size": _CLOUD_PAGE_SIZE})

    def datasets(self) -> Iterator[dict]:
        request = partial(
            self._base_request, endpoint=SodaEndpointFactory.datasets()
        )
        yield from fetch_all_pages(
            request, SodaCloudPagination, rate_limit=_RATE_LIMIT_MS
        )

    def checks(self) -> Iterator[dict]:
        request = partial(
            self._base_request, endpoint=SodaEndpointFactory.checks()
        )
        yield from fetch_all_pages(
            request, SodaCloudPagination, rate_limit=_RATE_LIMIT_MS
        )

    def fetch(self, asset: SodaAsset) -> Iterator:
        if asset == SodaAsset.DATASETS:
            return self.datasets()
        if asset == SodaAsset.CHECKS:
            return self.checks()
        raise ValueError(f"The asset {asset}, is not supported")
