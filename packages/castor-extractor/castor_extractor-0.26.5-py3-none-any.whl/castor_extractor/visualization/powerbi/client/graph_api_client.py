from collections.abc import Iterable, Iterator
from functools import partial
from http import HTTPStatus

from requests import HTTPError

from ....utils import (
    APIClient,
    RequestSafeMode,
    fetch_all_pages,
)
from .authentication import PowerBiBearerAuth
from .credentials import PowerbiCredentials
from .endpoints import GraphAPIEndpointFactory
from .pagination import GraphAPIPagination

VOLUME_IGNORED = 100
# there are special users (e.g. Tenant Administrators) that do not exist
# outside of Power BI, and hence cannot be fetched from Graph API
IGNORED_ERROR_CODES = (HTTPStatus.NOT_FOUND,)
GRAPH_SAFE_MODE = RequestSafeMode(
    max_errors=VOLUME_IGNORED,
    status_codes=IGNORED_ERROR_CODES,
)


class MicrosoftGraphAccessForbidden(Exception):
    def __init__(self):
        error_msg = (
            "The user does not have permissions to access Microsoft Graph."
        )
        super().__init__(error_msg)


class MicrosoftGraphPIClient(APIClient):
    def __init__(
        self,
        credentials: PowerbiCredentials,
    ):
        auth = PowerBiBearerAuth(credentials=credentials, scope_type="graph")
        super().__init__(
            auth=auth,
            safe_mode=GRAPH_SAFE_MODE,
        )
        self.endpoint_factory = GraphAPIEndpointFactory(
            login_url=credentials.login_url,
            api_base=credentials.graph_api_base,
        )

    def _group_members(self, group_id: str) -> list[dict]:
        """Get all transitive members of a single group"""
        request = partial(
            self._get,
            endpoint=self.endpoint_factory.transitive_group_members(group_id),
        )
        users = list(fetch_all_pages(request, GraphAPIPagination))
        return users

    def users_in_groups(self, group_ids: Iterable[str]) -> Iterator[dict]:
        """
        Returns the list of users that are part of the given groups.
        This may contain duplicate entries.
        Raises a custom Exception if the user does not have permissions to
        read group members.
        """
        for group_id in group_ids:
            try:
                yield from self._group_members(group_id)
            except HTTPError as err:
                if err.response.status_code == HTTPStatus.FORBIDDEN:
                    raise MicrosoftGraphAccessForbidden()
                raise
