import logging
from collections.abc import Iterator
from dataclasses import asdict
from typing import Any

from ....utils import load_file
from ....warehouse.abstract import TimeFilter
from ....warehouse.bigquery import BigQueryClient
from ..assets import (
    CountAsset,
)
from .credentials import CountCredentials

logger = logging.getLogger(__name__)

_QUERIES_FOLDER = "queries"


class CountClient(BigQueryClient):
    """
    Count.co does not currently provide an official API.
    Instead, metadata such as dashboards, users, and queries is made available through
    special metadata tables stored in BigQuery.

    This client extends `BigQueryClient` to access and interact with those metadata tables.
    """

    def __init__(self, credentials: CountCredentials):
        super().__init__(asdict(credentials))
        self.project_id = credentials.project_id
        self.dataset_id = credentials.dataset_id
        self.time_filter = TimeFilter.default()  # setting current date - 1

    def _load_query(self, asset: CountAsset) -> str:
        query = load_file(
            f"{_QUERIES_FOLDER}/{asset.name.lower()}.sql", __file__
        )
        return query.format(
            project_id=self.project_id,
            dataset_id=self.dataset_id,
            extract_date=self.time_filter.day,
        )

    def fetch(self, asset: CountAsset) -> Iterator[dict[str, Any]]:
        """
        Fetch the asset given as a param by running a BigQuery query.
        """
        logger.info(f"Running BigQuery query to fetch: {asset.name}")

        query_str = self._load_query(asset)
        job = self.client.query(query_str)
        results = job.result()

        for row in results:
            yield dict(row)
