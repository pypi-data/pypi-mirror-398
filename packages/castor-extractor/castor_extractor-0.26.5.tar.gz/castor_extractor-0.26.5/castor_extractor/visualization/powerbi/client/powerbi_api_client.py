import logging
from collections.abc import Iterator
from datetime import date
from functools import partial
from http import HTTPStatus
from time import sleep

import requests
from requests import HTTPError

from ....utils import (
    APIClient,
    fetch_all_pages,
    retry_request,
)
from .authentication import PowerBiBearerAuth
from .constants import Keys
from .credentials import PowerbiCredentials
from .endpoints import PowerBiEndpointFactory
from .pagination import PowerBIAPIPagination

POWERBI_DEFAULT_TIMEOUT_S = 30
# The route we use to fetch workspaces info can retrieve a maximum of
# 100 workspaces per call
# More: https://learn.microsoft.com/en-us/rest/api/power-bi/admin/workspace-info-post-workspace-info#request-body
METADATA_BATCH_SIZE = 100
POWERBI_SCAN_STATUS_DONE = "Succeeded"
POWERBI_SCAN_SLEEP_S = 1
POWERBI_SCAN_TIMEOUT_S = 60

MAX_RETRY_PAGES = 1
RETRY_PAGES_TIMEOUT_MS = 35 * 1000  # 35 seconds

KEYS_TO_HIDE = ("ClientIP", "UserAgent")

logger = logging.getLogger(__name__)


class PowerBIAPIClient(APIClient):
    def __init__(
        self,
        credentials: PowerbiCredentials,
    ):
        auth = PowerBiBearerAuth(credentials=credentials, scope_type="powerbi")
        super().__init__(
            auth=auth,
            timeout=POWERBI_DEFAULT_TIMEOUT_S,
        )
        self.endpoint_factory = PowerBiEndpointFactory(
            login_url=credentials.login_url,
            api_base=credentials.api_base,
        )

    def activity_events(self, day: date | None = None) -> Iterator[dict]:
        """
        Returns a list of activity events for the organization.
        https://learn.microsoft.com/en-us/power-bi/admin/service-admin-auditing#activityevents-rest-api
        - when no day is specified, fallback is yesterday
        """
        request = partial(
            self._get,
            endpoint=self.endpoint_factory.activity_events(day),
        )
        for event in fetch_all_pages(request, PowerBIAPIPagination):
            for key in KEYS_TO_HIDE:
                if key in event:
                    del event[key]
            yield event

    def datasets(self) -> Iterator[dict]:
        """
        Returns a list of datasets for the organization.
        https://learn.microsoft.com/en-us/rest/api/power-bi/admin/datasets-get-datasets-as-admin
        """
        yield from self._get(self.endpoint_factory.datasets())[Keys.VALUE]

    def dashboards(self) -> Iterator[dict]:
        """
        Returns a list of dashboards for the organization.
        https://learn.microsoft.com/en-us/rest/api/power-bi/admin/dashboards-get-dashboards-as-admin
        """
        yield from self._get(self.endpoint_factory.dashboards())[Keys.VALUE]

    @retry_request(
        status_codes=(HTTPStatus.TOO_MANY_REQUESTS,),
        max_retries=MAX_RETRY_PAGES,
        base_ms=RETRY_PAGES_TIMEOUT_MS,
    )
    def _pages(self, report_id: str) -> Iterator[dict]:
        """
        Extracts the pages of a report.
        This endpoint is very flaky and frequently returns 400 and 404 errors.
        After around 50 requests, it hits the rate limit and returns 429 Too Many Requests,
        which is why we retry it after a short delay.
        Timeouts are also common; we must skip them because the extraction task
        might take too long otherwise.
        """
        pages_endpoint = self.endpoint_factory.pages(report_id)
        return self._get(pages_endpoint, retry_on_timeout=False)[Keys.VALUE]

    def _get_accessible_workspace_ids(self) -> set[str]:
        """
        Returns the IDs of workspaces the credentials have access to.
        https://learn.microsoft.com/en-us/rest/api/power-bi/groups/get-groups
        """
        workspaces = self._get(self.endpoint_factory.groups())[Keys.VALUE]
        return {w[Keys.ID] for w in workspaces}

    def _get_pages_or_none(
        self, report: dict, accessible_workspace_ids: set[str]
    ) -> dict | None:
        report_id = report.get(Keys.ID)
        workspace_id = report.get(Keys.WORKSPACE_ID)

        if workspace_id not in accessible_workspace_ids:
            return None

        try:
            return self._pages(report_id)
        except (requests.HTTPError, requests.exceptions.Timeout) as e:
            logger.debug(e)
            return None

    def reports(self) -> Iterator[dict]:
        """
        Returns a list of reports for the organization.
        https://learn.microsoft.com/en-us/rest/api/power-bi/admin/reports-get-reports-as-admin

        For each report, it also attempts to extracts its pages. Unfortunately,
        the endpoint is not an Admin endpoint and therefore only works on
        reports beloning to workspaces that the credentials have access to.
        This may also take long enough for the token to expire, so it's
        force-refreshed at the end to avoid issues with the next requests.
        https://learn.microsoft.com/en-us/rest/api/power-bi/reports/get-pages
        """
        reports = self._get(self.endpoint_factory.reports())[Keys.VALUE]

        accessible_workspace_ids = self._get_accessible_workspace_ids()
        if not accessible_workspace_ids:
            logger.warning(
                "No accessible workspaces found. Skipping pages extraction."
            )
            return reports

        for report in reports:
            pages = self._get_pages_or_none(report, accessible_workspace_ids)
            if pages:
                report["pages"] = pages

        self._auth.refresh_token()
        return reports

    def _workspace_ids(self) -> list[str]:
        """
        Get workspaces ids from powerBI admin API.
        more: https://learn.microsoft.com/en-us/rest/api/power-bi/admin/workspace-info-get-modified-workspaces
        """
        params: dict[str, bool | str] = {
            Keys.INACTIVE_WORKSPACES: True,
            Keys.PERSONAL_WORKSPACES: True,
        }

        response = self._get(
            self.endpoint_factory.workspace_ids(),
            params=params,
        )

        return [x[Keys.ID] for x in response]

    def _get_scan_result(self, scan_id: int) -> Iterator[dict]:
        endpoint = self.endpoint_factory.metadata_scan_result(scan_id)
        yield from self._get(endpoint)[Keys.WORKSPACES]

    def _wait_for_scan_result(self, scan_id: int) -> bool:
        """
        Periodically checks the status of the metadata scan until the results
        are ready.
        """
        endpoint = self.endpoint_factory.metadata_scan_status(scan_id)
        total_waiting_time_s = 0

        while total_waiting_time_s < POWERBI_SCAN_TIMEOUT_S:
            try:
                result = self._get(endpoint)
            except HTTPError as e:
                logger.error(f"Scan {scan_id} failed. Error: {e}")
                return False

            if result[Keys.STATUS] == POWERBI_SCAN_STATUS_DONE:
                logger.info(f"scan {scan_id} ready")
                return True

            total_waiting_time_s += POWERBI_SCAN_SLEEP_S
            logger.info(
                f"Waiting {POWERBI_SCAN_SLEEP_S} sec for scan {scan_id} to be ready…",
            )
            sleep(POWERBI_SCAN_SLEEP_S)

        logger.warning(f"Scan {scan_id} timed out")
        return False

    def _create_scan(self, workspaces_ids: list[str]) -> int:
        """
        Tells the Power BI API to start an asynchronous metadata scan.
        Returns the scan's ID.
        https://learn.microsoft.com/en-us/rest/api/power-bi/admin/workspace-info-post-workspace-info
        """
        params = {
            "datasetExpressions": True,
            "datasetSchema": True,
            "datasourceDetails": True,
            "getArtifactUsers": True,
            "lineage": True,
        }
        request_body = {"workspaces": workspaces_ids}
        scan_id = self._post(
            self.endpoint_factory.metadata_create_scan(),
            params=params,
            data=request_body,
        )
        return scan_id[Keys.ID]

    def metadata(self) -> Iterator[dict]:
        """
        Fetch metadata by workspace. The metadata scanning is asynchronous and
        requires the following steps:
        - create the asynchronous scan
        - periodically check the scan status to know when it's finished
        - get the actual scan results
        https://learn.microsoft.com/en-us/power-bi/enterprise/service-admin-metadata-scanning
        """
        ids = self._workspace_ids()

        for index in range(0, len(ids), METADATA_BATCH_SIZE):
            batch_ids = ids[index : index + METADATA_BATCH_SIZE]
            scan_id = self._create_scan(batch_ids)
            self._wait_for_scan_result(scan_id)
            yield from self._get_scan_result(scan_id)
