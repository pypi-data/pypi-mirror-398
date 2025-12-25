import logging
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor

import requests

from ....utils import build_url
from ....utils.salesforce import SalesforceBaseClient
from ..assets import SalesforceReportingAsset
from .soql import queries

logger = logging.getLogger(__name__)

REQUIRING_URL_ASSETS = (
    SalesforceReportingAsset.REPORTS,
    SalesforceReportingAsset.DASHBOARDS,
    SalesforceReportingAsset.FOLDERS,
)

_CONCURRENT_THREADS = 50


class SalesforceReportingClient(SalesforceBaseClient):
    """
    Salesforce Reporting API client
    """

    def _get_asset_url(
        self, asset_type: SalesforceReportingAsset, asset: dict
    ) -> str | None:
        """
        Fetch the given Asset + add the corresponding URL.
        """

        if asset_type == SalesforceReportingAsset.DASHBOARDS:
            path = f"lightning/r/Dashboard/{asset['Id']}/view"
            return build_url(self._host, path)

        if asset_type == SalesforceReportingAsset.FOLDERS:
            path = asset["attributes"]["url"].lstrip("/")
            return build_url(self._host, path)

        if asset_type == SalesforceReportingAsset.REPORTS:
            path = f"lightning/r/Report/{asset['Id']}/view"
            return build_url(self._host, path)

        return None

    def _fetch_and_add_url(
        self, asset_type: SalesforceReportingAsset
    ) -> Iterator[dict]:
        assets = self._query_all(queries[asset_type])
        for asset in assets:
            url = self._get_asset_url(asset_type, asset)
            yield {**asset, "Url": url}

    def _metadata(self, report_id: str) -> dict | None:
        url = f"services/data/v60.0/analytics/reports/{report_id}/describe"
        try:
            metadata = self._get(url, retry_on_timeout=False)
            # pick only what we need to build the lineage
            columns = metadata["reportExtendedMetadata"]["detailColumnInfo"]
            return {
                "reportId": report_id,
                "detailColumnInfo": columns or dict(),
            }
        except (requests.HTTPError, requests.RequestException) as ex:
            # Extracting column metadata is used only for lineage purposes
            # and is non-critical. API errors are common during this step,
            # so we choose to skip them rather than fail the process. The same
            # rows consistently fail, and retries have proven ineffective.
            logger.info(ex)
            return None

    def _fetch_reports_metadata(self) -> Iterator[dict]:
        """
        Use the "describe" endpoint to extract report metadata.
        Keep only the detailColumnInfo, which is required for building the lineage.

        More info here:
        https://developer.salesforce.com/docs/atlas.en-us.api_analytics.meta/api_analytics/sforce_analytics_rest_api_getbasic_reportmetadata.htm
        https://www.notion.so/castordoc/Salesforce-Lineage-216a1c3d458580859888cf4ca2d7fa51?source=copy_link
        """
        # The "describe" endpoint requires report_ids. To avoid introducing
        # task dependencies, we opted to re-extract the reports.
        # It is fast anyway, since it's running a SQL query
        reports = self.fetch(SalesforceReportingAsset.REPORTS)
        report_ids = [report["Id"] for report in reports]

        # Calling "describe" on each report individually can be slow,
        # especially for accounts with thousands of reports. That's why
        # we use multithreading here — it significantly improves performance.
        with ThreadPoolExecutor(max_workers=_CONCURRENT_THREADS) as executor:
            fetch_results = executor.map(self._metadata, report_ids)

            for metadata in fetch_results:
                if not metadata:
                    continue
                yield metadata

    def fetch(self, asset: SalesforceReportingAsset) -> list[dict]:
        """
        Fetch Salesforce Reporting assets
        """
        logger.info(f"Starting extraction of {asset}")

        if asset in REQUIRING_URL_ASSETS:
            return list(self._fetch_and_add_url(asset))

        if asset == SalesforceReportingAsset.REPORTS_METADATA:
            return list(self._fetch_reports_metadata())

        return list(self._query_all(queries[asset]))
