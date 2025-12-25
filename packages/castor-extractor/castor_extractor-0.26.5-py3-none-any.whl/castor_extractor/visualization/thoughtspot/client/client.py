import logging
from collections.abc import Iterable, Iterator
from functools import partial

import requests
from requests import Response

from ....utils import (
    APIClient,
    BearerAuth,
    RequestSafeMode,
    build_url,
    fetch_all_pages,
    handle_response,
)
from ..assets import (
    ThoughtspotAsset,
)
from .credentials import (
    ThoughtspotCredentials,
)
from .endpoints import (
    ThoughtspotEndpointFactory,
)
from .pagination import METADATA_BATCH_SIZE, ThoughtSpotPagination

_AUTH_TIMEOUT_S = 60
_THOUGHTSPOT_HEADERS = {
    "X-Requested-By": "ThoughtSpot",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
# https://docs.thoughtspot.com/cloud/latest/object-usage-liveboard
_OBJECT_USAGE_LIVEBOARD = "Object Usage"
_ANSWER_USAGE_VIZ = "Answer Usage, by User"
# https://docs.thoughtspot.com/cloud/latest/user-adoption
_USER_ADOPTION_LIVEBOARD = "User Adoption"
_LIVEBOARD_USAGE_VIZ = "Popular Liveboards Last 30 Days"
# By default, no errors are ignored for the moment
THOUGHTSPOT_SAFE_MODE = RequestSafeMode()


logger = logging.getLogger(__name__)


class ThoughtspotBearerAuth(BearerAuth):
    def __init__(self, host: str, token_payload: dict[str, str]):
        auth_endpoint = ThoughtspotEndpointFactory.authentication()
        self.authentication_url = build_url(host, auth_endpoint)
        self.token_payload = token_payload

    def fetch_token(self):
        token_api_path = self.authentication_url
        token_response = requests.post(
            token_api_path, data=self.token_payload, timeout=_AUTH_TIMEOUT_S
        )
        return handle_response(token_response)["token"]


class ThoughtspotClient(APIClient):
    def __init__(
        self,
        credentials: ThoughtspotCredentials,
        safe_mode: RequestSafeMode | None = None,
    ):
        auth = ThoughtspotBearerAuth(
            host=credentials.base_url,
            token_payload=credentials.dict(),
        )
        super().__init__(
            host=credentials.base_url,
            auth=auth,
            headers=_THOUGHTSPOT_HEADERS,
            safe_mode=safe_mode or THOUGHTSPOT_SAFE_MODE,
        )

    def _metadata_search(
        self,
        metadata_type: str,
        identifier: str | None = None,
    ) -> Iterator[dict]:
        """
        Yields assets of the given asset type, and optionally filters on a
        specific identifier.
        """
        offset = 0

        while True:
            search_filters = {
                "metadata": [{"type": metadata_type}],
                "include_details": True,
                "record_size": METADATA_BATCH_SIZE,
                "record_offset": offset,
            }
            if identifier:
                search_filters["metadata"] = {
                    "identifier": identifier,
                    "type": metadata_type,
                }

            metadata = self._post(
                ThoughtspotEndpointFactory.metadata_search(),
                data=search_filters,
            )
            yield from metadata
            if len(metadata) < METADATA_BATCH_SIZE:
                break
            offset = offset + METADATA_BATCH_SIZE

    def _get_all_answers(self) -> Iterator[dict]:
        yield from self._metadata_search(metadata_type="ANSWER")

    def _get_all_liveboards(self) -> Iterator[dict]:
        yield from self._metadata_search(metadata_type="LIVEBOARD")

    def _get_all_columns(self) -> Iterator[dict]:
        yield from self._metadata_search(metadata_type="LOGICAL_COLUMN")

    def _get_all_tables(self) -> Iterator[dict]:
        yield from self._metadata_search(metadata_type="LOGICAL_TABLE")

    def _get_usages(
        self,
        liveboard_name: str,
        visualization_name: str,
    ) -> Iterator[list[list]]:
        """
        Yields the data of a given visualization in the given liveboard.
        ThoughtSpot maintains two system liveboards with stats about data usage,
        which are useful to compute view counts and popularity.
        """
        usage_liveboard = next(
            self._metadata_search(
                metadata_type="LIVEBOARD", identifier=liveboard_name
            )
        )
        liveboard_id = usage_liveboard["metadata_id"]

        def handler(response: Response) -> dict:
            response_dict = response.json()
            contents = response_dict.get("contents", [])
            if not contents:
                logger.warning("No data found in response")
                return dict()
            return contents[0]

        request = partial(
            self._post,
            endpoint=ThoughtspotEndpointFactory.liveboard_data(),
            data={
                "metadata_identifier": liveboard_id,
                "visualization_identifiers": [visualization_name],
                "record_offset": 0,
                "record_size": METADATA_BATCH_SIZE,
            },
            handler=handler,
        )
        yield from fetch_all_pages(request, ThoughtSpotPagination)

    def _get_answer_usages(self) -> Iterator[dict]:
        """
        Returns the usage data of saved Answers, which is found in a visualization
        of the "Object Usage" liveboard.
        Each data row returned by the API is transformed from a list into a dictionary.
        The columns are explicitly listed here because in the API response,
        there is a mismatch between the number of column names and the number
        of values per data row.
        """
        data: Iterable[list[list]] = self._get_usages(
            liveboard_name=_OBJECT_USAGE_LIVEBOARD,
            visualization_name=_ANSWER_USAGE_VIZ,
        )
        columns = (
            "Answer name",
            "Number of unique users",
            "Count of object interactions",
        )
        for row in data:
            yield dict(zip(columns, row))

    def _get_liveboards_usages(self) -> Iterator[dict]:
        """
        Returns the usage data of Liveboards, which is found in a visualization
        of the "User Adoption" liveboard.
        Each data row returned by the API is transformed from a list into a dictionary.
        See `_get_answer_usages` regarding the columns list.
        """
        data: Iterable[list[list]] = self._get_usages(
            liveboard_name=_USER_ADOPTION_LIVEBOARD,
            visualization_name=_LIVEBOARD_USAGE_VIZ,
        )
        columns = ("Pinboard", "Unique Number of User", "Pinboard Views")
        for row in data:
            yield dict(zip(columns, row))

    def fetch(self, asset: ThoughtspotAsset) -> Iterator[dict]:
        if asset == ThoughtspotAsset.ANSWERS:
            yield from self._get_all_answers()

        if asset == ThoughtspotAsset.ANSWER_USAGES:
            yield from self._get_answer_usages()

        if asset == ThoughtspotAsset.LIVEBOARDS:
            yield from self._get_all_liveboards()

        if asset == ThoughtspotAsset.LIVEBOARD_USAGES:
            yield from self._get_liveboards_usages()

        if asset == ThoughtspotAsset.LOGICAL_TABLES:
            yield from self._get_all_tables()
