import logging
from collections.abc import Iterable, Iterator
from functools import partial

from ....utils import (
    APIClient,
    BasicAuth,
    fetch_all_pages,
)
from ..assets import (
    ConfluenceAsset,
)
from .credentials import ConfluenceCredentials
from .endpoints import ConfluenceEndpointFactory
from .pagination import ConfluencePagination

logger = logging.getLogger(__name__)

_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}
_STATUS_ARCHIVED = "archived"
_TYPE_PERSONAL = "personal"


class ConfluenceClient(APIClient):
    def __init__(
        self,
        credentials: ConfluenceCredentials,
        include_archived_spaces: bool = False,
        include_personal_spaces: bool = False,
        space_ids_allowed: set[str] | None = None,
        space_ids_blocked: set[str] | None = None,
    ):
        self.account_id = credentials.account_id
        auth = BasicAuth(
            username=credentials.username, password=credentials.token
        )
        super().__init__(
            auth=auth,
            host=credentials.base_url,
            headers=_HEADERS,
        )

        self.include_archived_spaces = include_archived_spaces
        self.include_personal_spaces = include_personal_spaces
        self.space_ids_allowed = space_ids_allowed or set()
        self.space_ids_blocked = space_ids_blocked or set()

    def databases(self, database_ids: Iterable[str]) -> Iterator[dict]:
        """
        Extracts all given databases
        """
        for _id in database_ids:
            database = self._get(
                endpoint=ConfluenceEndpointFactory.database(_id),
            )
            yield database

    def folders(self, folder_ids: Iterable[str]) -> Iterator[dict]:
        """
        Extracts all given folders and their parent folders.
        """
        candidate_ids = set(folder_ids)
        seen = set()

        while candidate_ids:
            folder_id = candidate_ids.pop()
            if folder_id in seen:
                continue

            seen.add(folder_id)
            folder = self._get(
                endpoint=ConfluenceEndpointFactory.folder(folder_id),
            )
            yield folder

            parent_type = folder.get("parentType")
            if parent_type == "folder":
                folder_id = folder["parentId"]
                if folder_id not in seen:
                    candidate_ids.add(folder["parentId"])

            if not parent_type:
                logger.info(f"folder with unknown parent: {folder_id}")

    def pages(self):
        """Extracts all pages from all relevant Spaces."""
        for space in self.spaces():
            space_id = space["id"]
            request = partial(
                self._get,
                endpoint=ConfluenceEndpointFactory.pages(space_id),
            )
            yield from fetch_all_pages(request, ConfluencePagination)

    def spaces(self) -> Iterator[dict]:
        """
        Returns the spaces meeting the conditions defined by the settings.

        If `space_ids_allowed` is not empty, only matching spaces are returned.

        Otherwise, all spaces are filtered by excluding the following:
          * The space is in the blocked list
          * The space is personal (type=personal) and skip_personal_spaces is True
          * The space is archived (status=archived) and skip_archived_spaces is True
        """
        request = partial(
            self._get,
            endpoint=ConfluenceEndpointFactory.spaces(),
        )
        spaces = list(fetch_all_pages(request, ConfluencePagination))

        if self.space_ids_allowed:
            yield from (
                space
                for space in spaces
                if space["id"] in self.space_ids_allowed
            )
            return

        for space in spaces:
            space_id = space["id"]
            type_ = space["type"]
            status = space["status"]

            if space_id in self.space_ids_blocked:
                continue

            if status == _STATUS_ARCHIVED and not self.include_archived_spaces:
                continue

            if type_ == _TYPE_PERSONAL and not self.include_personal_spaces:
                continue

            yield space

    def users(self):
        request_body = {"accountIds": [self.account_id]}
        request = partial(
            self._post,
            endpoint=ConfluenceEndpointFactory.users(),
            data=request_body,
        )
        yield from fetch_all_pages(request, ConfluencePagination)

    def fetch(
        self,
        asset: ConfluenceAsset,
        *,
        folder_ids: Iterator[str] | None = None,
        database_ids: Iterator[str] | None = None,
    ) -> Iterator[dict]:
        """Returns the needed metadata for the queried asset"""
        if asset == ConfluenceAsset.FOLDERS:
            assert folder_ids is not None
            yield from self.folders(folder_ids)

        elif asset == ConfluenceAsset.DATABASES:
            assert database_ids is not None
            yield from self.databases(database_ids)

        elif asset == ConfluenceAsset.PAGES:
            yield from self.pages()

        elif asset == ConfluenceAsset.USERS:
            yield from self.users()

        else:
            raise ValueError(f"This asset {asset} is unknown")
