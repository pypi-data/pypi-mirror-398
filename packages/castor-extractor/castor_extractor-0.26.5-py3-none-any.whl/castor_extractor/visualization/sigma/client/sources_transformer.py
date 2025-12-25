import logging
from collections.abc import Callable, Iterator
from http import HTTPStatus
from time import sleep
from typing import TYPE_CHECKING

from ....utils import fetch_all_pages, retry_request
from .endpoints import SigmaEndpointFactory
from .pagination import SigmaTokenPagination

if TYPE_CHECKING:
    from .client import SigmaClient

logger = logging.getLogger(__name__)

RETRY_CODES = (
    HTTPStatus.TOO_MANY_REQUESTS,
    HTTPStatus.SERVICE_UNAVAILABLE,
)

SIGMA_CONNECTION_PATH_MAX_RETRY = 1
SIGMA_CONNECTION_PATH_SLEEP_MS = 30_000

SIGMA_SOURCES_MAX_RETRY = 1
SIGMA_SOURCES_RETRY_SLEEP_MS = 30_000
SIGMA_SOURCES_REQUEST_SLEEP_S = 0.4


class SigmaSourcesTransformer:
    """Retrieves asset sources and enhances them with additional information."""

    def __init__(
        self, api_client: "SigmaClient", table_id_key: str = "inodeId"
    ):
        self.api_client = api_client
        self.table_id_key = table_id_key

    @retry_request(
        status_codes=RETRY_CODES,
        max_retries=SIGMA_CONNECTION_PATH_MAX_RETRY,
        base_ms=SIGMA_CONNECTION_PATH_SLEEP_MS,
    )
    def _get_connection_path(self, table_id: str) -> dict:
        """Retrieves the connection path for a given table id"""
        return self.api_client._get(
            endpoint=SigmaEndpointFactory.connection_path(table_id)
        )

    def _map_table_id_to_connection_path(
        self, all_sources: list
    ) -> dict[str, dict]:
        """Maps a table id to its connection and path information."""
        logger.info("Mapping table ids to connection and path information")

        unique_table_ids = {
            source[self.table_id_key]
            for asset_sources in all_sources
            for source in asset_sources.get("sources", [])
            if source["type"] == "table"
        }

        return {
            table_id: self._get_connection_path(table_id)
            for table_id in unique_table_ids
        }

    def _enhance_table_source(self, source: dict, table_to_path: dict) -> dict:
        """
        Combines a single table source with its connection and path information.
        """
        if source["type"] != "table":
            return source

        path_info = table_to_path.get(source[self.table_id_key], {})
        source["connectionId"] = path_info.get("connectionId")
        source["path"] = path_info.get("path")
        return source

    def _transform_sources(
        self, all_sources: list, table_to_path: dict
    ) -> Iterator[dict]:
        """
        Yields all sources, with table sources being enhanced with additional information.
        """
        logger.info("Merging sources with table information")

        for asset_sources in all_sources:
            enhanced_sources = [
                self._enhance_table_source(source, table_to_path)
                for source in asset_sources["sources"]
            ]

            yield {
                "asset_id": asset_sources["asset_id"],
                "sources": enhanced_sources,
            }

    @retry_request(
        status_codes=RETRY_CODES,
        max_retries=SIGMA_SOURCES_MAX_RETRY,
        base_ms=SIGMA_SOURCES_RETRY_SLEEP_MS,
    )
    def _fetch_asset_sources(
        self,
        asset_id: str,
        endpoint: Callable[[str], str],
        with_pagination: bool,
    ) -> dict:
        """Fetches sources for a single asset."""
        endpoint_url = endpoint(asset_id)

        if with_pagination:
            request = self.api_client._get_paginated(endpoint=endpoint_url)
            pages_generator = fetch_all_pages(
                request=request,
                pagination_model=SigmaTokenPagination,
                rate_limit=SIGMA_SOURCES_REQUEST_SLEEP_S,
            )
            sources = list(pages_generator)
        else:
            sources = self.api_client._get(endpoint=endpoint_url)
            sleep(SIGMA_SOURCES_REQUEST_SLEEP_S)

        return {"asset_id": asset_id, "sources": sources}

    def _get_all_sources(
        self,
        endpoint: Callable[[str], str],
        asset_ids: set[str],
        with_pagination: bool = False,
    ) -> Iterator[dict]:
        """Returns transformed sources for the given assets"""
        all_sources = [
            self._fetch_asset_sources(asset_id, endpoint, with_pagination)
            for asset_id in asset_ids
        ]

        table_to_path = self._map_table_id_to_connection_path(all_sources)

        yield from self._transform_sources(all_sources, table_to_path)

    def get_datamodel_sources(self, datamodels: list[dict]) -> Iterator[dict]:
        asset_ids = {datamodel["dataModelId"] for datamodel in datamodels}
        yield from self._get_all_sources(
            endpoint=SigmaEndpointFactory.datamodel_sources,
            asset_ids=asset_ids,
            with_pagination=True,
        )

    def get_dataset_sources(self, datasets: list[dict]) -> Iterator[dict]:
        asset_ids = {dataset["datasetId"] for dataset in datasets}
        yield from self._get_all_sources(
            endpoint=SigmaEndpointFactory.dataset_sources, asset_ids=asset_ids
        )

    def get_workbook_sources(self, workbooks: list[dict]) -> Iterator[dict]:
        asset_ids = {workbook["workbookId"] for workbook in workbooks}
        yield from self._get_all_sources(
            endpoint=SigmaEndpointFactory.workbook_sources, asset_ids=asset_ids
        )
