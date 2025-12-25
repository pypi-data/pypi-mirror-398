import logging
import sys
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from looker_sdk.error import SDKError
from tqdm import tqdm  # type: ignore

from ...utils import RetryStrategy, deep_serialize, retry
from . import ApiClient
from .assets import LookerAsset

logger = logging.getLogger(__name__)

LOOKER_EXCEPTIONS = (SDKError,)
RETRY_COUNT = 2
RETRY_BASE_MS = 1
RETRY_JITTER_MS = 1
RETRY_STRATEGY = RetryStrategy.LINEAR


@retry(
    exceptions=LOOKER_EXCEPTIONS,
    max_retries=RETRY_COUNT,
    base_ms=RETRY_BASE_MS,
    jitter_ms=RETRY_JITTER_MS,
    strategy=RETRY_STRATEGY,
)
def _make_api_request(
    client: ApiClient,
    asset: LookerAsset,
    folder_id: str,
) -> list:
    """
    Calls the appropriate Looker API endpoint to retrieve either Looks or
    Dashboards withered by the given folder ID.
    """
    if asset == LookerAsset.LOOKS:
        return client.looks(folder_id=folder_id)
    return client.dashboards(folder_id=folder_id)


class MultithreadingFetcher:
    def __init__(
        self,
        folder_ids: set[str],
        client: ApiClient,
        thread_pool_size: int,
        log_to_stdout: bool,
    ):
        self._folder_ids = folder_ids
        self._client = client
        self._thread_pool_size = thread_pool_size
        self._log_to_stdout = log_to_stdout

    def _progress_bar(self, fetch_results: Iterable, total: int) -> tqdm:
        """Create a tqdm progress bar with the appropriate logs destination"""
        file = sys.stderr

        if self._log_to_stdout:
            file = sys.stdout

        return tqdm(fetch_results, total=total, file=file)

    def fetch_assets(self, asset: LookerAsset) -> Iterable[dict]:
        """
        Yields serialized Looks or Dashboards with a request per folder ID.
        Requests are parallelised.
        Explore names associated to dashboards are saved for later use.
        """
        total_assets_count = 0
        total_folders = len(self._folder_ids)

        _fetch = partial(_make_api_request, self._client, asset)

        with ThreadPoolExecutor(max_workers=self._thread_pool_size) as executor:
            fetch_results = executor.map(_fetch, self._folder_ids)

            for results in self._progress_bar(fetch_results, total_folders):
                for result in results:
                    if not result:
                        continue

                    total_assets_count += len(result)
                    yield deep_serialize(result)

        logger.info(f"Fetched {total_assets_count} {asset.value}")
