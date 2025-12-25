import logging
from typing import Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter, Retry, RetryError
from requests.exceptions import HTTPError

from ..assets import EXPORTED_FIELDS, QlikAsset
from .constants import (
    ASSET_PATHS,
    RESPONSE_DICT_EXPECTED_MSG,
    RESPONSE_LIST_EXPECTED_MSG,
    REST_API_BASE_PATH,
    RETRY_BACKOFF_FACTOR,
    RETRY_COUNTS,
    RETRY_STATUSES,
)
from .engine import QlikCredentials

logger = logging.getLogger(__name__)

Response = Union[dict, list[dict]]


def _session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=RETRY_COUNTS,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        status_forcelist=RETRY_STATUSES,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    return session


def _check_next_page_url(links: dict, current_page_url: str) -> str | None:
    next_page = links.get("next")
    if not next_page:
        return None

    next_page_url = next_page["href"]
    if next_page_url == current_page_url:
        return None

    return next_page_url


def _asset_path(asset: QlikAsset) -> str:
    assert asset in ASSET_PATHS, f"{asset} is not available through REST-API"
    return ASSET_PATHS[asset]


class RestApiClient:
    """
    Client class to connect to Qlik REST API and retrieve Qlik assets

    API documentation: https://qlik.dev/apis/#rest
    """

    def __init__(
        self,
        credentials: QlikCredentials,
        except_http_error_statuses: list[int] | None = None,
    ):
        self._server_url = credentials.base_url
        self._api_key = credentials.api_key
        self._session = _session()
        self._except_http_error_statuses = except_http_error_statuses or []
        self._authenticate()

    def _authenticate(self):
        auth_header = {"Authorization": "Bearer " + self._api_key}
        self._session.headers.update(auth_header)

    @property
    def server_url(self) -> str:
        """Returns attribute server url"""
        return self._server_url

    def _url(self, asset_path: str, app_id: str | None = None) -> str:
        """
        Formats the full url with a specific asset path

        Optionally the asset path can be provided an `app_id` when the url must
        be scoped on an source. Beware that the asset_path must then be formattable
        with an "app_id" argument.
        """
        if app_id:
            asset_path = asset_path.format(app_id=app_id)

        path = REST_API_BASE_PATH + asset_path
        return urljoin(self._server_url, path)

    def _handle_http_error(self, error: HTTPError):
        status_code = error.response.status_code
        if status_code in self._except_http_error_statuses:
            logger.warning(error)
            return None
        raise error

    def _call(self, url: str) -> Response | None:
        try:
            response = self._session.get(url)
            response.raise_for_status()
            return response.json()
        except RetryError as error:
            logger.warning(error)
            return None
        except HTTPError as error:
            return self._handle_http_error(error)

    def _pager(self, first_page_url: str) -> list[dict]:
        current_page_url = first_page_url

        data: list[dict] = []
        while current_page_url:
            response = self._call(current_page_url)
            if not response:
                return data
            assert isinstance(response, dict), RESPONSE_DICT_EXPECTED_MSG
            data.extend(response["data"])

            links = response["links"]
            next_page_url = _check_next_page_url(links, current_page_url)
            if not next_page_url:
                return data

            current_page_url = next_page_url
        return data

    def get(self, asset: QlikAsset) -> list[dict]:
        """
        Calls the route corresponding to the asset and returns the list of
        corresponding data
        """
        asset_path = _asset_path(asset)
        url = self._url(asset_path)
        data = self._pager(url)

        def _filter_fields(row: dict) -> dict:
            return {key: row.get(key) for key in EXPORTED_FIELDS[asset]}

        return [_filter_fields(row) for row in data]

    def get_with_scope(self, asset: QlikAsset, app_id: str) -> list[dict]:
        """
        Calls the route corresponding to the asset scoped on an app_id and
        returns the corresponding data
        """
        asset_path = ASSET_PATHS[asset]
        url = self._url(asset_path, app_id=app_id)
        response = self._call(url)
        if not response:
            return []
        assert isinstance(response, list), RESPONSE_LIST_EXPECTED_MSG
        return response

    def data_connections(self) -> list[dict]:
        """
        Returns the list of data Connections

        doc: https://qlik.dev/apis/rest/data-connections/#%23%2Fentries%2Fv1%2Fdata-connections-get
        """
        return self.get(QlikAsset.CONNECTIONS)

    def spaces(self) -> list[dict]:
        """
        Returns the list of Spaces

        doc: https://qlik.dev/apis/rest/spaces/#%23%2Fentries%2Fspaces-get
        """
        return self.get(QlikAsset.SPACES)

    def users(self) -> list[dict]:
        """
        Returns the list of Users

        doc: https://qlik.dev/apis/rest/users/#%23%2Fentries%2Fusers-get
        """
        return self.get(QlikAsset.USERS)

    def apps(self) -> list[dict]:
        """
        Returns the list of Apps

        doc: https://qlik.dev/apis/rest/items/#%23%2Fentries%2Fitems-get
        """
        return self.get(QlikAsset.APPS)

    def data_lineage(self, app_id: str) -> list[dict]:
        """
        Returns the data lineage for a given source

        doc: https://qlik.dev/apis/rest/apps/#%23%2Fentries%2Fapps%2F-appId%2Fdata%2Flineage-get
        """
        return self.get_with_scope(QlikAsset.LINEAGE, app_id=app_id)
