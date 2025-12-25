import logging
from typing import Optional, cast

import requests
from requests.auth import HTTPBasicAuth

from ....utils import retry
from ..assets import (
    ASSETS_WITH_OWNER,
    EXPORTED_FIELDS,
    ModeAnalyticsAsset as Asset,
)
from ..errors import (
    MissingPrerequisiteError,
    UnexpectedApiResponseError,
    check_errors,
)
from .constants import (
    CLIENT_NAME,
    RETRY_BASE_MS,
    RETRY_COUNT,
    RETRY_EXCEPTIONS,
    RETRY_JITTER_MS,
    RETRY_STRATEGY,
)
from .credentials import ModeCredentials

logger = logging.getLogger(__name__)

URL_TEMPLATE = "{host}/api"

RawData = list[dict]
Tokens = Optional[list[str]]


class Client:
    """
    Connect to Mode Analytics API and fetch main assets.
    https://mode.com/developer/api-reference/introduction/
    """

    def __init__(
        self,
        credentials: ModeCredentials,
    ):
        self._credentials = credentials
        self._session = requests.Session()

    def authenticate(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self._credentials.token, self._credentials.secret)

    def _check_connection(self):
        authentication = self.authenticate()
        url = self._url(with_workspace=False) + "/account"
        response = self._session.get(url, auth=authentication)
        self._handle_response(response)
        logger.info("Authentication succeeded.")

    @staticmethod
    def name() -> str:
        """return the name of the client"""
        return CLIENT_NAME

    @staticmethod
    def _handle_response(
        response: requests.Response,
        *,
        resource_name: str | None = None,
    ) -> RawData:
        check_errors(response)
        result = response.json()

        if "_embedded" not in result:
            # some calls return data directly
            return result

        # most of calls return data in ["_embedded"]["resource_name"] node
        try:
            embedded = cast(dict, result["_embedded"])
            return cast(list, embedded[resource_name])
        except (ValueError, KeyError):
            raise UnexpectedApiResponseError(resource_name, result)

    def base_url(self) -> str:
        """Return base_url from credentials"""
        return f"{self._credentials.host}/{self._credentials.workspace}"

    def _url(
        self,
        with_workspace: bool = True,
        space: str | None = None,
        report: str | None = None,
        resource_name: str | None = None,
    ) -> str:
        url = URL_TEMPLATE.format(host=self._credentials.host)
        if with_workspace:
            url += f"/{self._credentials.workspace}"
        if space:
            url += f"/spaces/{space}"
        if report:
            url += f"/reports/{report}"
        if resource_name:
            url += f"/{resource_name}"
        return url

    @retry(
        exceptions=RETRY_EXCEPTIONS,
        max_retries=RETRY_COUNT,
        base_ms=RETRY_BASE_MS,
        jitter_ms=RETRY_JITTER_MS,
        strategy=RETRY_STRATEGY,
    )
    def _call(
        self,
        *,
        with_workspace: bool = True,
        space: str | None = None,
        report: str | None = None,
        resource_name: str | None = None,
    ) -> RawData:
        authentication = self.authenticate()
        url = self._url(with_workspace, space, report, resource_name)
        logger.info(f"Calling {url}")
        response = self._session.get(url, auth=authentication)
        return self._handle_response(response, resource_name=resource_name)

    def _reports(self, spaces: RawData | None) -> RawData:
        reports: RawData = []
        # the only way to fetch reports is to loop on spaces
        # https://mode.com/developer/api-reference/analytics/reports/#listReportsInSpace
        if not spaces:
            raise MissingPrerequisiteError(
                fetched=Asset.REPORT,
                missing=Asset.COLLECTION,
            )
        for space in spaces:
            space_token = space["token"]
            # example: https://modeanalytics.com/api/{workspace}/spaces/{space_token}/reports
            result = self._call(space=space_token, resource_name="reports")
            reports.extend(result)
        return reports

    def _queries(self, reports: RawData | None) -> RawData:
        queries: RawData = []
        if not reports:
            raise MissingPrerequisiteError(
                fetched=Asset.QUERY,
                missing=Asset.REPORT,
            )
        for report in reports:
            report_token = report["token"]
            result = self._call(report=report_token, resource_name="queries")
            for query in result:
                query["report_token"] = report_token
            queries.extend(result)
        return queries

    def _members(self) -> RawData:
        members: RawData = []
        # the only way to fetch members is to loop on memberships
        # https://mode.com/developer/api-reference/management/workspace-memberships/#listMemberships
        memberships = self._call(resource_name="memberships")
        for mb in memberships:
            # then we fetch users one by one, using their {username}
            # why without workspace? because users can belong to several companies
            # example: https://modeanalytics.com/api/john_doe
            result = self._call(
                resource_name=mb["member_username"],
                with_workspace=False,
            )
            members.append(cast(dict, result))
        return members

    @staticmethod
    def _post_processing(asset: Asset, data: RawData) -> RawData:
        filtered = []
        for row in data:
            if asset in ASSETS_WITH_OWNER:
                # extract creator from _links
                creator_href = row["_links"]["creator"]["href"]
                # remove "api/" to keep only the username
                row["creator"] = creator_href[5:]
            # keep only exported fields
            new = {key: row.get(key) for key in EXPORTED_FIELDS[asset]}
            filtered.append(new)
        return filtered

    def fetch(
        self,
        asset: Asset,
        *,
        additional_data: RawData | None = None,
    ) -> RawData:
        """
        Fetch the given asset.

        :additional_data must be provided in certain cases
        - to fetch REPORTS, provide the list of COLLECTIONS
        - to fetch QUERIES, provide the list of REPORTS
        Otherwise MissingPrerequisiteError will be raised.

        It means that extracting all data must be executed in a certain order:
        ```
          members = client.fetch(Asset.MEMBER)
          datasources = client.fetch(Asset.DATASOURCE)
          collections = client.fetch(Asset.COLLECTION)
          reports = client.fetch(Asset.REPORT, additional_data=collections)
          queries = client.fetch(Asset.QUERY, additional_data=reports)
        ```
        """
        logger.info(f"Starting extraction for {asset.name}...")
        # specific calls
        if asset == Asset.REPORT:
            result = self._reports(spaces=additional_data)
        elif asset == Asset.MEMBER:
            result = self._members()
        elif asset == Asset.QUERY:
            result = self._queries(reports=additional_data)
        else:
            # generic calls
            # example: https://modeanalytics.com/api/{workspace}/spaces
            # example: https://modeanalytics.com/api/{workspace}/data_sources
            result = self._call(resource_name=str(asset.value))
        logger.info(f"{len(result)} rows extracted")
        return self._post_processing(asset, result)
