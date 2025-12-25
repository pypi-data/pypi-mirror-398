import logging
from collections.abc import Callable, Generator, Iterable, Iterator
from contextlib import contextmanager
from functools import partial
from http import HTTPStatus

from requests import HTTPError, ReadTimeout

from ....utils import (
    APIClient,
    RequestSafeMode,
    fetch_all_pages,
)
from ..assets import SigmaAsset
from .authentication import SigmaBearerAuth
from .credentials import SigmaCredentials
from .endpoints import SigmaEndpointFactory
from .pagination import (
    SIGMA_API_LIMIT,
    SIGMA_QUERIES_PAGINATION_LIMIT,
    SigmaPagination,
)
from .sources_transformer import SigmaSourcesTransformer

logger = logging.getLogger(__name__)

_CONTENT_TYPE = "application/x-www-form-urlencoded"

_DATA_ELEMENTS: tuple[str, ...] = (
    "input-table",
    "pivot-table",
    "table",
    "visualization",
    "viz",
)

_SIGMA_TIMEOUT_S = 300

_SIGMA_HEADERS = {
    "Content-Type": _CONTENT_TYPE,
}

_VOLUME_IGNORED = 10_000
_IGNORED_ERROR_CODES = (
    HTTPStatus.BAD_REQUEST,
    HTTPStatus.BAD_GATEWAY,
    HTTPStatus.INTERNAL_SERVER_ERROR,
    HTTPStatus.CONFLICT,
    HTTPStatus.NOT_FOUND,
    HTTPStatus.FORBIDDEN,
)
SIGMA_SAFE_MODE = RequestSafeMode(
    max_errors=_VOLUME_IGNORED,
    status_codes=_IGNORED_ERROR_CODES,
)


@contextmanager
def _handle_api_errors(error_details: str) -> Generator[None, None, None]:
    """
    Context manager that handles common Sigma API errors: ReadTimeout and
    Http 503 Server Unavailable errors. These exceptions are skipped.
    """
    try:
        yield
    except ReadTimeout:
        logging.warning(f"ReadTimeout: {error_details}")
        return
    except HTTPError as e:
        if e.response.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
            logging.warning(f"503 Service unavailable: {error_details}")
            return
        raise


class SigmaClient(APIClient):
    def __init__(self, credentials: SigmaCredentials):
        auth = SigmaBearerAuth(
            host=credentials.host,
            token_payload=credentials.token_payload,
        )
        super().__init__(
            host=credentials.host,
            auth=auth,
            headers=_SIGMA_HEADERS,
            timeout=_SIGMA_TIMEOUT_S,
            safe_mode=SIGMA_SAFE_MODE,
        )

    def _get_paginated(
        self,
        endpoint: str,
        limit: int = SIGMA_API_LIMIT,
    ) -> Callable:
        """
        Sigma’s API does not experience random timeouts, unlike some other APIs.
        However, extracting queries from certain workbooks can take a
        significant amount of time.
        Previously, when a timeout occurred, the system would retry multiple
        times — even though we knew it would eventually fail due to the inherent
        slowness of the operation.
        These retries only delayed the inevitable failure without adding value.
        To address this, we've disabled retries on timeout and instead adjusted
        the page size when extracting queries.
        """
        return partial(
            self._get,
            retry_on_timeout=False,  # explained in the docstring
            endpoint=endpoint,
            params={"limit": limit},
        )

    def _get_all_datamodels(self) -> Iterator[dict]:
        request = self._get_paginated(
            endpoint=SigmaEndpointFactory.datamodels()
        )
        yield from fetch_all_pages(request, SigmaPagination)

    def _get_all_datasets(self) -> Iterator[dict]:
        request = self._get_paginated(endpoint=SigmaEndpointFactory.datasets())
        yield from fetch_all_pages(request, SigmaPagination)

    def _get_all_files(self) -> Iterator[dict]:
        request = self._get_paginated(endpoint=SigmaEndpointFactory.files())
        yield from fetch_all_pages(request, SigmaPagination)

    def _get_all_members(self) -> Iterator[dict]:
        request = self._get_paginated(endpoint=SigmaEndpointFactory.members())
        yield from fetch_all_pages(request, SigmaPagination)

    def _get_all_workbooks(self) -> Iterator[dict]:
        request = self._get_paginated(endpoint=SigmaEndpointFactory.workbooks())
        yield from fetch_all_pages(request, SigmaPagination)

    @staticmethod
    def _safe_fetch_elements(
        elements: Iterator[dict],
        workbook_id: str,
        page_id: str,
    ) -> Iterator[dict]:
        """
        Safely iterates over elements with ReadTimeout & 503 Server Unavailable
        handling. In case of said error, it skips the entire rest of the page.
        """
        error_details = f"error for page {page_id} in workbook {workbook_id}"

        with _handle_api_errors(error_details):
            for element in elements:
                if element.get("type") not in _DATA_ELEMENTS:
                    continue
                yield {
                    **element,
                    "workbook_id": workbook_id,
                    "page_id": page_id,
                }

    def _get_elements_per_page(
        self, page: dict, workbook_id: str
    ) -> Iterator[dict]:
        page_id = page["pageId"]
        request = self._get_paginated(
            SigmaEndpointFactory.elements(workbook_id, page_id)
        )
        elements = fetch_all_pages(request, SigmaPagination)
        yield from self._safe_fetch_elements(elements, workbook_id, page_id)

    def _get_all_elements(self, workbooks: list[dict]) -> Iterator[dict]:
        for workbook in workbooks:
            workbook_id = workbook["workbookId"]

            request = self._get_paginated(
                SigmaEndpointFactory.pages(workbook_id)
            )
            pages = fetch_all_pages(request, SigmaPagination)

            for page in pages:
                yield from self._get_elements_per_page(
                    page=page, workbook_id=workbook_id
                )

    @staticmethod
    def _yield_deduplicated_queries(
        queries: Iterable[dict], workbook_id: str
    ) -> Iterator[dict]:
        """
        Returns unique queries for a workbook. This is necessary because the API
        unfortunately returns duplicate entries for some workbook elements.
        """
        seen_elements = set()

        for query in queries:
            element_id = query["elementId"]
            if element_id in seen_elements:
                continue

            seen_elements.add(element_id)
            yield {**query, "workbook_id": workbook_id}

    def _get_all_queries(self, workbooks: list[dict]) -> Iterator[dict]:
        for workbook in workbooks:
            workbook_id = workbook["workbookId"]

            request = self._get_paginated(
                SigmaEndpointFactory.queries(workbook_id),
                limit=SIGMA_QUERIES_PAGINATION_LIMIT,
            )
            queries = fetch_all_pages(request, SigmaPagination)

            error_details = f"error for workbook {workbook_id}"
            with _handle_api_errors(error_details):
                yield from self._yield_deduplicated_queries(
                    queries, workbook_id
                )

    def _get_all_datamodel_sources(
        self, datamodels: list[dict]
    ) -> Iterator[dict]:
        yield from SigmaSourcesTransformer(
            self, table_id_key="tableId"
        ).get_datamodel_sources(datamodels)

    def _get_all_dataset_sources(self, datasets: list[dict]) -> Iterator[dict]:
        yield from SigmaSourcesTransformer(self).get_dataset_sources(datasets)

    def _get_all_workbook_sources(
        self, workbooks: list[dict]
    ) -> Iterator[dict]:
        yield from SigmaSourcesTransformer(self).get_workbook_sources(workbooks)

    def fetch(
        self,
        asset: SigmaAsset,
        datamodels: list[dict] | None = None,
        datasets: list[dict] | None = None,
        workbooks: list[dict] | None = None,
    ) -> Iterator[dict]:
        """Returns the needed metadata for the queried asset"""
        if asset == SigmaAsset.DATAMODELS:
            yield from self._get_all_datamodels()

        elif asset == SigmaAsset.DATAMODEL_SOURCES:
            if datamodels is None:
                raise ValueError(
                    "Missing data models to extract data model sources"
                )

            yield from self._get_all_datamodel_sources(datamodels)

        elif asset == SigmaAsset.DATASETS:
            yield from self._get_all_datasets()

        elif asset == SigmaAsset.DATASET_SOURCES:
            if datasets is None:
                raise ValueError("Missing datasets to extract dataset sources")

            yield from self._get_all_dataset_sources(datasets)

        elif asset == SigmaAsset.ELEMENTS:
            if workbooks is None:
                raise ValueError("Missing workbooks to extract elements")

            yield from self._get_all_elements(workbooks)

        elif asset == SigmaAsset.FILES:
            yield from self._get_all_files()

        elif asset == SigmaAsset.MEMBERS:
            yield from self._get_all_members()

        elif asset == SigmaAsset.QUERIES:
            if workbooks is None:
                raise ValueError("Missing workbooks to extract queries")

            yield from self._get_all_queries(workbooks)

        elif asset == SigmaAsset.WORKBOOKS:
            yield from self._get_all_workbooks()

        elif asset == SigmaAsset.WORKBOOK_SOURCES:
            if workbooks is None:
                raise ValueError(
                    "Missing workbooks to extract workbook sources"
                )

            yield from self._get_all_workbook_sources(workbooks)

        else:
            raise ValueError(f"This asset {asset} is unknown")

    def test_connection(self) -> None:
        """Use credentials & verify requesting the API doesn't raise an error"""
        self._auth.refresh_token()
