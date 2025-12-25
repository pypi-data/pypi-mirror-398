import logging
from collections.abc import Iterator
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Any

import requests

from ....utils import (
    RequestSafeMode,
    at_midnight,
    batch_of_length,
    current_date,
    empty_iterator,
    handle_response,
    past_date,
    retry,
    timestamp_ms,
)
from ..assets import DomoAsset
from .credentials import DomoCredentials
from .endpoints import Endpoint, EndpointFactory
from .pagination import Pagination

RawData = Iterator[dict]

DOMO_PUBLIC_URL = "https://api.domo.com"
DEFAULT_TIMEOUT = 120
TOKEN_EXPIRATION_SECONDS = timedelta(seconds=3000)  # auth token lasts 1 hour


# Safe Mode
VOLUME_IGNORED = 10
IGNORED_ERROR_CODES = (
    HTTPStatus.BAD_REQUEST,
    HTTPStatus.NOT_FOUND,
)
DOMO_SAFE_MODE = RequestSafeMode(
    max_errors=VOLUME_IGNORED,
    status_codes=IGNORED_ERROR_CODES,
)

_RETRY_EXCEPTIONS = [
    requests.exceptions.ConnectTimeout,
    requests.exceptions.ReadTimeout,
]
_RETRY_COUNT = 2
_RETRY_BASE_MS = 10 * 60 * 1000  # 10 minutes

_PARENT_FOLDER = "/Dashboards"

_CARDS_BATCH_SIZE = 100

logger = logging.getLogger(__name__)


class DomoClient:
    """
    Connect to Domo API and fetch main assets.
    https://developer.domo.com/portal/8ba9aedad3679-ap-is#platform-oauth-apis
    """

    def __init__(
        self,
        credentials: DomoCredentials,
        safe_mode: RequestSafeMode | None = None,
    ):
        self._authentication = credentials.authentication
        self._bearer_headers: dict | None = None
        self._session = requests.session()
        self._token_creation_time: datetime = datetime.min
        self._endpoint_factory = EndpointFactory(credentials.base_url)
        self._private_headers = credentials.private_headers
        self._timeout = DEFAULT_TIMEOUT
        self.base_url = credentials.base_url
        self.cloud_id = credentials.cloud_id
        self.safe_mode = safe_mode or DOMO_SAFE_MODE

    def _token_expired(self) -> bool:
        token_lifetime = datetime.now() - self._token_creation_time
        return token_lifetime > TOKEN_EXPIRATION_SECONDS

    def _bearer_auth(self) -> dict:
        if self._bearer_headers and not self._token_expired():
            return self._bearer_headers

        logger.info("Refreshing authentication token...")

        basic_authentication = self._authentication
        endpoint = self._endpoint_factory.authentication

        response = self._session.get(
            endpoint.url(),
            auth=basic_authentication,
            timeout=self._timeout,
        )
        response.raise_for_status()
        result = response.json()

        bearer_token = result["access_token"]
        self._bearer_headers = {"authorization": f"Bearer {bearer_token}"}
        self._token_creation_time = datetime.now()

        return self._bearer_headers

    @retry(
        exceptions=_RETRY_EXCEPTIONS,
        max_retries=_RETRY_COUNT,
        base_ms=_RETRY_BASE_MS,
    )
    def _get(
        self,
        endpoint: Endpoint,
        params: dict | None = None,
        asset_id: str | None = None,
    ) -> Any:
        params = params if params else {}
        is_private = endpoint.is_private
        headers = self._private_headers if is_private else self._bearer_auth()

        response = self._session.get(
            url=endpoint.url(asset_id),
            headers=headers,
            params=params,
            timeout=self._timeout,
        )

        return handle_response(response, self.safe_mode)

    def _get_element(
        self,
        endpoint: Endpoint,
        params: dict | None = None,
        asset_id: str | None = None,
    ) -> dict:
        """Used when the response only contains one element"""
        return self._get(endpoint, params, asset_id)

    def _get_many(
        self,
        endpoint: Endpoint,
        params: dict | None = None,
        asset_id: str | None = None,
    ) -> list[dict]:
        """Used when the response contains multiple elements"""
        return self._get(endpoint, params, asset_id)

    def _get_paginated(self, endpoint: Endpoint) -> list[dict]:
        """Used when the response is paginated and need iterations"""
        pagination = Pagination()
        all_results: list[dict] = []

        while pagination.needs_increment:
            params = {**pagination.params, **endpoint.params}
            results = self._get_many(endpoint=endpoint, params=params)
            all_results.extend(results)
            number_of_items = len(results)
            pagination.increment_offset(number_of_items)

        return all_results

    def _cards_metadata(self, card_ids: list[int]) -> Iterator[dict]:
        # batch to avoid hitting the URL max length
        for batch_card_ids in batch_of_length(card_ids, _CARDS_BATCH_SIZE):
            endpoint = self._endpoint_factory.cards_metadata(batch_card_ids)
            yield from self._get_element(endpoint)

    def _datasources(self, card_ids: list[int]) -> RawData:
        """Yields all distinct datasources associated to the given cards"""
        if not card_ids:
            return empty_iterator()

        processed: set[str] = set()
        for card in self._cards_metadata(card_ids):
            for datasource in card["datasources"]:
                id_ = datasource["dataSourceId"]
                if id_ in processed:
                    continue
                yield {
                    "id": id_,
                    "name": datasource["dataSourceName"],
                    "type": datasource["dataType"],
                }
                processed.add(id_)

    def _process_pages(
        self,
        page_tree: list[dict],
        parent_path: str = _PARENT_FOLDER,
    ) -> Iterator[dict]:
        """Recursively fetch pages while building the folder architecture"""
        if not page_tree:
            return empty_iterator()

        for page in page_tree:
            page_id = page.get("id")
            page_name = page.get("name")
            if not (page_id and page_name):
                logger.debug(f"This page has no id nor name: {page}")
                continue

            page_children = page.get("children", list)

            detail = self._get_element(
                self._endpoint_factory.pages,
                asset_id=page_id,
            )

            if not detail:
                continue

            datasources = self._datasources(detail.get("cardIds", []))
            yield {
                **detail,
                "datasources": list(datasources),
                "path": parent_path,
                "base_url": self.base_url,
            }
            yield from self._process_pages(
                page_tree=page_children,
                parent_path=f"{parent_path}/{page_name}",
            )

    def _link_table_to_dataset(self, dataset: dict, dataset_id: str) -> dict:
        if not self.cloud_id:
            return dataset

        lineage_endpoint = self._endpoint_factory.table_lineage(
            dataset_id=dataset_id,
            cloud_id=self.cloud_id,
        )
        dataset_table_lineage = self._get_element(lineage_endpoint)

        return {**dataset, **dataset_table_lineage}

    def _pages(self) -> RawData:
        page_hierarchy = self._get_paginated(self._endpoint_factory.pages)
        yield from self._process_pages(page_hierarchy)

    def _datasets(self) -> RawData:
        dataset_list = self._get_paginated(self._endpoint_factory.datasets)

        for dataset in dataset_list:
            dataset_id = dataset.get("id")
            if not dataset_id:
                continue

            dataset_detail = self._get_element(
                endpoint=self._endpoint_factory.datasets,
                asset_id=dataset_id,
            )

            yield {
                **self._link_table_to_dataset(
                    dataset=dataset_detail,
                    dataset_id=dataset_id,
                ),
                "base_url": self.base_url,
            }

    def _unique_datasets(self) -> RawData:
        ids_encountered: set[str] = set()
        for dataset in self._datasets():
            dataset_id = dataset.get("id")
            if not dataset_id or dataset_id in ids_encountered:
                continue
            ids_encountered.add(dataset_id)
            yield dataset

    def _users(self) -> RawData:
        user_list = self._get_paginated(self._endpoint_factory.users)
        for user in user_list:
            user_id = user.get("id")
            if not user_id:
                continue
            yield self._get_element(
                endpoint=self._endpoint_factory.users,
                asset_id=user_id,
            )

    def _audit(self) -> RawData:
        yesterday = timestamp_ms(at_midnight(past_date(1)))
        today = timestamp_ms(at_midnight(current_date()))
        yield from self._get_paginated(
            self._endpoint_factory.audit(yesterday, today)
        )

    def _dataflows(self) -> RawData:
        dataflows = self._get_many(self._endpoint_factory.dataflows)
        for dataflow in dataflows:
            dataflow_id = dataflow.get("id")
            if not dataflow_id:
                continue
            yield self._get_element(self._endpoint_factory.lineage(dataflow_id))

    def fetch(self, asset: DomoAsset) -> RawData:
        """Returns the needed metadata for the queried asset"""
        if asset == DomoAsset.PAGES:
            yield from self._pages()

        elif asset == DomoAsset.DATASETS:
            yield from self._unique_datasets()

        elif asset == DomoAsset.USERS:
            yield from self._users()

        elif asset == DomoAsset.AUDIT:
            yield from self._audit()

        elif asset == DomoAsset.DATAFLOWS:
            yield from self._dataflows()

        else:
            raise ValueError(f"This asset {asset} is unknown")
