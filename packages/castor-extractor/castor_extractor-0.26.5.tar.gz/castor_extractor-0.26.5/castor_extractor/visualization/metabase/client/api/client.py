import logging
from collections.abc import Iterator
from http import HTTPStatus
from typing import Any, cast

import requests
from requests import HTTPError

from .....utils import (
    JsonType,
    RequestSafeMode,
    SerializedAsset,
    handle_response,
)
from ...assets import EXPORTED_FIELDS, MetabaseAsset
from ...errors import MetabaseLoginError, SuperuserCredentialsRequired
from ...types import IdsType
from ..shared import DETAILS_KEY, get_dbname_from_details
from .credentials import MetabaseApiCredentials

logger = logging.getLogger(__name__)

# Safe mode
VOLUME_IGNORED = 5
IGNORED_ERROR_CODES = (
    HTTPStatus.BAD_REQUEST,
    HTTPStatus.NOT_FOUND,
)
METABASE_SAFE_MODE = RequestSafeMode(
    max_errors=VOLUME_IGNORED,
    status_codes=IGNORED_ERROR_CODES,
)

URL_TEMPLATE = "{base_url}/api/{endpoint}"

ROOT_KEY = "root"
CARDS_KEY = "dashcards"
CARDS_KEY_DEPRECATED = "ordered_cards"  # prior to v0.48 of Metabase
DATA_KEY = "data"


class ApiClient:
    """
    Connect to Metabase API and fetch main assets.
    Superuser credentials are required.
    https://www.metabase.com/docs/latest/api-documentation.html
    """

    def __init__(
        self,
        credentials: MetabaseApiCredentials,
        safe_mode: RequestSafeMode | None = None,
    ):
        self.base_url = credentials.base_url

        self._credentials = credentials
        self._session = requests.Session()
        self._session_id = self._login()
        self.safe_mode = safe_mode or METABASE_SAFE_MODE
        self._check_permissions()  # verify that the given user is superuser

    @staticmethod
    def name() -> str:
        """return the name of the client"""
        return "Metabase/API"

    def _url(self, endpoint: str) -> str:
        return URL_TEMPLATE.format(
            base_url=self.base_url,
            endpoint=endpoint,
        )

    def _headers(self) -> dict:
        return {
            "X-Metabase-Session": self._session_id,
            "Content-type": "application/x-www-form-urlencoded",
        }

    @staticmethod
    def _answer(response: Any):
        answer = response
        if isinstance(answer, dict) and DATA_KEY in answer:
            # v0.41 of Metabase introduced embedded data for certain calls
            # {'data': [{ }, ...] , 'total': 15, 'limit': None, 'offset': None}"
            return answer[DATA_KEY]
        return answer

    def _call(self, endpoint: str) -> JsonType:
        url = self._url(endpoint)
        headers = self._headers()
        response = self._session.get(url=url, headers=headers)
        response = handle_response(response, safe_mode=self.safe_mode)
        return self._answer(response)

    def _check_permissions(self) -> None:
        try:
            # This endpoint requires superuser credentials
            self._call("collection/graph")
        except HTTPError as err:
            if err.response.status_code == 403:  # forbidden
                raise SuperuserCredentialsRequired(
                    credentials_info=self._credentials,
                    error_details=err.args,
                )
            raise

    def _login(self) -> str:
        url = self._url("session")
        payload = {
            "username": self._credentials.user,
            "password": self._credentials.password,
        }
        response = self._session.post(url, json=payload)
        logger.info(f"Getting session_id: {response.json()}")

        if not response.json().get("id"):
            raise MetabaseLoginError(
                credentials_info=self._credentials,
                error_details=response.json(),
            )

        return response.json()["id"]

    def _fetch_ids(self, asset: MetabaseAsset) -> IdsType:
        ids: IdsType = []
        results = self._call(endpoint=asset.name.lower())
        for res in cast(list, results):
            assert isinstance(res, dict)
            ids.append(res["id"])
        return ids

    def _dashboards(self) -> Iterator[dict]:
        collection_ids = self._fetch_ids(MetabaseAsset.COLLECTION)
        for _id in collection_ids:
            collection = self._call(f"collection/{_id}/items?models=dashboard")
            if not collection:
                continue

            seen_dashboard_ids: set[int] = set()

            for dashboard in cast(SerializedAsset, collection):
                if dashboard.get("model") != "dashboard":
                    # This is to maintain compatibility with older versions
                    # where ?models=dashboard has no effects
                    continue

                dashboard_id = dashboard.get("id")
                if not dashboard_id:
                    continue

                if dashboard_id not in seen_dashboard_ids:
                    seen_dashboard_ids.add(dashboard_id)
                    yield cast(dict, self._call(f"dashboard/{dashboard_id}"))

    @staticmethod
    def _collection_specifics(collections: SerializedAsset) -> SerializedAsset:
        # remove the root folder
        def _is_not_root(collection: dict) -> bool:
            return collection.get("id") != ROOT_KEY

        return list(filter(_is_not_root, collections))

    @staticmethod
    def _database_specifics(databases: SerializedAsset) -> SerializedAsset:
        for db in databases:
            # superuser privileges are mandatory, this field should be present
            assert DETAILS_KEY in db
            details = db[DETAILS_KEY]
            db["dbname"] = get_dbname_from_details(details)

        return databases

    @staticmethod
    def _dashboard_cards(dashboards: SerializedAsset) -> Iterator[dict]:
        for d in dashboards:
            d_cards = d.get(CARDS_KEY) or d.get(CARDS_KEY_DEPRECATED) or []
            yield from d_cards

    def fetch(self, asset: MetabaseAsset) -> SerializedAsset:
        """fetches the given asset"""
        if asset == MetabaseAsset.DASHBOARD:
            assets = list(self._dashboards())

        elif asset == MetabaseAsset.DASHBOARD_CARDS:
            dashboards = list(self._dashboards())
            assets = list(self._dashboard_cards(dashboards))

        else:
            answer = self._call(asset.name.lower())
            assets = cast(list, answer)

        if asset == MetabaseAsset.DATABASE:
            assets = self._database_specifics(assets)

        if asset == MetabaseAsset.COLLECTION:
            assets = self._collection_specifics(assets)

        logger.info(f"Fetching {asset.name} ({len(assets)} results)")

        # keep interesting fields
        return [
            {key: e.get(key) for key in EXPORTED_FIELDS[asset]} for e in assets
        ]
