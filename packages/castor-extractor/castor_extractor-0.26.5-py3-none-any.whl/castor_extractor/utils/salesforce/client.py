import logging
from collections.abc import Iterator
from functools import partial
from http import HTTPStatus

import requests
from requests import HTTPError, Response

from ...utils import (
    APIClient,
    BearerAuth,
    build_url,
    fetch_all_pages,
    handle_response,
)
from .constants import DEFAULT_API_VERSION, DEFAULT_PAGINATION_LIMIT
from .credentials import SalesforceCredentials
from .pagination import SalesforcePagination

logger = logging.getLogger(__name__)

SALESFORCE_TIMEOUT_S = 120


class SalesforceBadRequestError(HTTPError):
    """
    Custom Exception to print the response's text when an error occurs
    during Salesforce's authentication.
    """

    def __init__(self, response: Response):
        text = response.text
        message = (
            f"{response.status_code} Client Error: {response.reason} for url: {response.url}"
            f"\nResponse text: {text}"
        )
        super().__init__(message, response=response)


class SalesforceAuth(BearerAuth):
    _AUTH_ENDPOINT = "services/oauth2/token"

    def __init__(self, credentials: SalesforceCredentials):
        self._host = credentials.base_url
        self._token_payload = credentials.token_request_payload()

    def fetch_token(self) -> str | None:
        """
        Fetches the access token from Salesforce using the provided credentials.
        A custom Exception is raised if the request fails with a 400 status code.
        """
        url = build_url(self._host, self._AUTH_ENDPOINT)
        response = requests.post(url, "POST", params=self._token_payload)

        if response.status_code == HTTPStatus.BAD_REQUEST:
            raise SalesforceBadRequestError(response)

        handled_response = handle_response(response)
        return handled_response["access_token"]


class SalesforceBaseClient(APIClient):
    """
    Salesforce API client.
    https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_rest.htm
    """

    api_version = DEFAULT_API_VERSION
    pagination_limit = DEFAULT_PAGINATION_LIMIT

    PATH_TPL = "services/data/v{version}/{suffix}"

    def __init__(self, credentials: SalesforceCredentials):
        auth = SalesforceAuth(credentials)
        super().__init__(
            host=credentials.base_url, auth=auth, timeout=SALESFORCE_TIMEOUT_S
        )

    def _endpoint(self, suffix: str) -> str:
        path = self.PATH_TPL.format(version=self.api_version, suffix=suffix)
        return path

    @property
    def query_endpoint(self) -> str:
        """Returns the query API url"""
        return self._endpoint("query")

    @property
    def tooling_endpoint(self) -> str:
        """Returns the tooling API url"""
        return self._endpoint("tooling/query")

    def _query_all(self, query: str) -> Iterator[dict]:
        """
        Run a SOQL query over salesforce API.

        more: https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_query.htm
        """
        request = partial(
            self._get,
            endpoint=self.query_endpoint,
            params={"q": query},
        )
        yield from fetch_all_pages(request, SalesforcePagination)
