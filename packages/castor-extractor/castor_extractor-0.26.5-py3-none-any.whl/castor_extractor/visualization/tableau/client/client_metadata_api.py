import functools
import itertools
import json
import logging
from collections.abc import Iterator

import requests
import tableauserverclient as TSC  # type: ignore
from tableauserverclient.server.endpoint.exceptions import (
    InternalServerError,
    NonXMLResponseError,
)

from ....utils import SerializedAsset, batch_of_length
from ..assets import TableauAsset
from ..constants import DEFAULT_PAGE_SIZE
from .errors import TableauApiError, TableauApiTimeout
from .gql_queries import FIELDS_QUERIES, GQL_QUERIES, QUERY_TEMPLATE
from .smart_pagination import SmartPagination

logger = logging.getLogger(__name__)

# increase the value when extraction is too slow
# decrease the value when timeouts arise
_CUSTOM_PAGE_SIZE: dict[TableauAsset, int] = {
    # fields are light but volumes are bigger
    TableauAsset.FIELD: 1000,
    # tables are sometimes heavy
    TableauAsset.TABLE: 50,
}

_TIMEOUT_MESSAGES = (
    "Execution canceled because timeout of 30000 millis was reached",
    # From experience, this internal error actually corresponds to a timeout
    "Internal Server Error(s) while executing query",
)


_BATCH_SIZE = 1000


def _format_filter_ids(filter_ids: list[str]) -> str:
    # "id_1", "id_2", ...
    formatted_filter_ids = ", ".join([f'"{id_}"' for id_ in filter_ids])

    # { idWithin: ["id_1", "id_2", ...] }
    return f"{{ idWithin: [{formatted_filter_ids}] }}"


def _is_timeout(error: dict) -> bool:
    error_message = error.get("message")
    return error_message in _TIMEOUT_MESSAGES


def _is_warning(error: dict) -> bool:
    extensions = error.get("extensions")
    if not extensions:
        return False

    severity = extensions.get("severity")
    if not severity:
        return False

    return severity.lower() == "warning"


def _check_errors(answer: dict) -> None:
    """
    Handle errors in graphql response:
    - return None when there's no errors in the answer
    - raise TableauApiTimeout if any of the errors is a timeout
    - else raise TableauApiError if any of the errors is critical
    - return None otherwise
    More info about Tableau errors:
    https://help.tableau.com/current/api/metadata_api/en-us/docs/meta_api_errors.html#other-errors
    """
    if "errors" not in answer:
        return

    errors = answer["errors"]

    has_timeout_errors = False
    has_critical_errors = False

    for error in errors:
        if _is_timeout(error):
            has_timeout_errors = True
            continue

        if _is_warning(error):
            # in this case, the answer contains the data anyway
            # just display the warning
            logger.warning(error)
            continue

        # at this point, it's not a timeout error
        # besides, it's not a warning (severity is either "error" or Unknown)
        has_critical_errors = True

    if has_timeout_errors:
        raise TableauApiTimeout(errors)
    if has_critical_errors:
        raise TableauApiError(errors)

    return None


_RETRYABLE_ERRORS = (
    InternalServerError,
    NonXMLResponseError,
    TableauApiTimeout,
    requests.exceptions.ReadTimeout,
)


def _is_relationship_service_war_exception(exception: Exception) -> bool:
    """
    Detects a specific NonXMLResponseError that occurs when Tableau's
    relationship-service-war endpoint responds with a 401 error due to
    concurrent API calls using the same authentication token.

    This issue is a known Tableau bug: when two metadata API calls happen
    simultaneously with the same token, Tableau may return a JSON payload
    instead of XML, wrapped in a NonXMLResponseError. Unlike other
    NonXMLResponseError cases, this one should **not** be retried — retrying
    will loop indefinitely and hide the real underlying token issue. Instead,
    callers should surface the exception and show logs to the user.

    More context:
    https://commtableau.my.site.com/s/question/0D54T00000dXBeRSAW/bug-report-unable-to-reauthenticate-once-the-token-expires

    """
    if not isinstance(exception, NonXMLResponseError):
        return False

    # raw bytes: b'{"timestamp":...}'
    error_bytes = exception.args[0]

    # Decode bytes to string
    error_str = error_bytes.decode("utf-8")
    # transform to JSON
    error_json = json.loads(error_str)

    status = error_json.get("status") or ""
    path = error_json.get("path") or ""

    return status == 401 and path == "/relationship-service-war/graphql"


def _gql_query_scroll(
    server,
    resource: str,
    fields: str,
    filter_: str,
    page_size: int,
    show_progress: bool,
) -> Iterator[SerializedAsset]:
    """
    Iterate over GQL query results, handling pagination and cursor

    We have a retry strategy when timeout issues arise.
    It's a known issue on Tableau side, still waiting for their fix:
    https://issues.salesforce.com/issue/a028c00000zKahoAAC/undefined
    """

    def _call(first: int, offset: int) -> dict:
        query = QUERY_TEMPLATE.format(
            resource=resource,
            fields=fields,
            filter=filter_,
            first=first,
            offset=offset,
        )
        answer = server.metadata.query(query)
        _check_errors(answer)
        return answer["data"][f"{resource}Connection"]

    current_offset = 0
    skipped_count = 0
    smart_pagination = SmartPagination(initial_page_size=page_size)
    while True:
        try:
            payload = _call(
                first=smart_pagination.page_size,
                offset=current_offset,
            )
            yield payload["nodes"]
            smart_pagination.next()

            current_offset += len(payload["nodes"])
            if show_progress:
                total = payload["totalCount"]
                logger.info(f"Extracted {current_offset}/{total} {resource}")

            if not payload["pageInfo"]["hasNextPage"]:
                break
        except _RETRYABLE_ERRORS as exception:
            if _is_relationship_service_war_exception(exception):
                raise
            logger.warning(f"Retryable exception: {exception}")
            if smart_pagination.page_size > 1:
                smart_pagination.reduce_page_size()
                continue

            logger.warning("Skipping asset because of TableauServer Timeout")
            skipped_count += 1
            current_offset += 1
            smart_pagination.reset()

    if skipped_count > 0:
        logger.info(f"Partial extraction - skipped {skipped_count} rows")


def _deduplicate(result_pages: Iterator[SerializedAsset]) -> SerializedAsset:
    """
    Sometimes assets are duplicated, which triggers UniqueViolation errors
    during store_all down the line.

    We suspect the offset pagination to be the root cause, because we had no
    problem until recently, when we switched from cursor pagination to offset
    pagination (for performance reasons)
    https://help.tableau.com/current/api/metadata_api/en-us/docs/meta_api_examples.html#pagination

    This is a straightforward solution to remove these duplicates directly at
    extraction.
    We don't show warnings because duplicates are expected, and we keep only
    the first occurrence since those duplicates are probably identical.
    """
    deduplicated: SerializedAsset = []
    seen_ids: set[str] = set()
    for page in result_pages:
        for asset in page:
            asset_id = asset["id"]
            if asset_id in seen_ids:
                # skip duplicate
                continue
            deduplicated.append(asset)
            seen_ids.add(asset_id)
    return deduplicated


class TableauClientMetadataApi:
    """
    Calls the MetadataAPI, using graphQL
    https://help.tableau.com/current/api/metadata_api/en-us/reference/index.html
    """

    def __init__(
        self,
        server: TSC.Server,
        override_page_size: int | None = None,
    ):
        self._server = server
        self._override_page_size = override_page_size

    def call(
        self,
        resource: str,
        fields: str,
        page_size: int = DEFAULT_PAGE_SIZE,
        show_progress: bool = True,
        filter_ids: list[str] | None = None,
    ) -> SerializedAsset:
        """
        Executes a GraphQL query against Tableau metadata API and returns
        deduplicated results.

        This method wraps the low-level pagination logic with retry handling,
        timeout management, optional batch skipping for error-prone assets,
        and post-processing to remove duplicate assets caused by offset
        pagination.

        This method handles two layers of chunking:
        1. ID-based batching: when `filter_ids` is provided, it is automatically
           split into batches of 1,000 to avoid query-size limits.
           Each batch is queried independently, then merged.

        2. Offset pagination: each batch (or the full resource when no
           `filter_ids` are given) is paginated using `page_size` via
           _gql_query_scroll()

        Results from all pages are concatenated and deduplicated.
        """

        scroll = functools.partial(
            _gql_query_scroll,
            server=self._server,
            resource=resource,
            fields=fields,
            page_size=page_size,
            show_progress=show_progress,
        )
        if filter_ids is None:
            # no ids –> run a single paginated query with an empty filter
            data = scroll(filter_="{}")
        else:
            # When IDs are provided:
            #   - Split IDs into manageable batches
            #   - Convert each batch into a GraphQL filter string
            #   - Query each batch independently
            filter_batches = (
                _format_filter_ids(ids)
                for ids in batch_of_length(filter_ids, _BATCH_SIZE)
            )
            data = itertools.chain.from_iterable(
                # Chain results from all batches.
                # Pagination progress is suppressed because it becomes too noisy
                # batching already emits sufficient logging.
                scroll(filter_=f, show_progress=False)
                for f in filter_batches
            )

        return _deduplicate(data)

    def _page_size(self, asset: TableauAsset) -> int:
        return (
            self._override_page_size
            or _CUSTOM_PAGE_SIZE.get(asset)
            or DEFAULT_PAGE_SIZE
        )

    def _fetch_fields(self) -> SerializedAsset:
        result: SerializedAsset = []
        page_size = self._page_size(TableauAsset.FIELD)
        for resource, fields in FIELDS_QUERIES:
            current = self.call(
                resource,
                fields,
                page_size,
            )
            result.extend(current)
        return result

    def fetch(
        self,
        asset: TableauAsset,
        filter_ids: list[str] | None = None,
    ) -> SerializedAsset:
        if asset == TableauAsset.FIELD:
            return self._fetch_fields()

        page_size = self._page_size(asset)
        resource, fields = GQL_QUERIES[asset]
        return self.call(
            resource=resource,
            fields=fields,
            page_size=page_size,
            filter_ids=filter_ids,
        )
