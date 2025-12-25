from collections.abc import Iterator
from functools import partial
from http import HTTPStatus

from ....utils import (
    APIClient,
    BearerAuth,
    RequestSafeMode,
    deduplicate,
    fetch_all_pages,
)
from ..assets import NotionAsset
from .constants import CASTOR_NOTION_USER_AGENT, NOTION_BASE_URL, NOTION_VERSION
from .credentials import NotionCredentials
from .endpoints import NotionEndpointFactory
from .pagination import NotionPagination

VOLUME_IGNORED = 10
IGNORED_ERROR_CODES = (HTTPStatus.BAD_GATEWAY, HTTPStatus.NOT_FOUND)
NOTION_SAFE_MODE = RequestSafeMode(
    max_errors=VOLUME_IGNORED,
    status_codes=IGNORED_ERROR_CODES,
)
NOTION_BASE_HEADERS = {
    "Notion-Version": NOTION_VERSION,
    "User-Agent": CASTOR_NOTION_USER_AGENT,
}

NOTION_DEFAULT_TIMEOUT_S = 180


def _search_filter(asset: str) -> dict[str, dict[str, str]]:
    return {"filter": {"value": asset, "property": "object"}}


class NotionAuth(BearerAuth):
    def __init__(self, token: str):
        self.token = token

    def fetch_token(self):
        return self.token


class NotionClient(APIClient):
    def __init__(
        self,
        credentials: NotionCredentials,
        safe_mode: RequestSafeMode | None = None,
    ):
        auth = NotionAuth(token=credentials.token)
        super().__init__(
            host=NOTION_BASE_URL,
            auth=auth,
            headers=NOTION_BASE_HEADERS,
            safe_mode=safe_mode or NOTION_SAFE_MODE,
            timeout=NOTION_DEFAULT_TIMEOUT_S,
        )

    def users(self) -> Iterator[dict]:
        """
        Yield all Notion users, deduplicated by user ID.
        """
        request = partial(self._get, endpoint=NotionEndpointFactory.users())
        all_users = fetch_all_pages(request, NotionPagination)
        return deduplicate("id", all_users)

    def _page_listing(self) -> Iterator[dict]:
        request = partial(
            self._post,
            endpoint=NotionEndpointFactory.search(),
            data=_search_filter("page"),
        )
        yield from fetch_all_pages(request, NotionPagination)

    def _blocks(self, block_id: str) -> Iterator[dict]:
        request = partial(
            self._get,
            endpoint=NotionEndpointFactory.blocks(block_id),
        )
        yield from fetch_all_pages(request, NotionPagination)

    def databases(self) -> Iterator[dict]:
        request = partial(
            self._post,
            endpoint=NotionEndpointFactory.search(),
            data=_search_filter("database"),
        )
        yield from fetch_all_pages(request, NotionPagination)

    def recursive_blocks(self, block_id: str) -> Iterator[dict]:
        """Fetch recursively all children blocks of a given block or page"""
        blocks = self._blocks(block_id)
        for block in blocks:
            if block["has_children"] and block.get("type") != "child_page":
                children = self.recursive_blocks(block["id"])
                block["child_blocks"] = list(children)

            yield block

    def pages(self) -> Iterator[dict]:
        """Fetch all pages with its whole content"""
        for page in self._page_listing():
            if page.get("object") == "database":
                # Notion Search API filter for page doesn't work
                continue
            content = list(self.recursive_blocks(page["id"]))
            page["child_blocks"] = content
            yield page

    def fetch(self, asset: NotionAsset) -> Iterator[dict]:
        """Returns the needed metadata for the queried asset"""
        if asset == NotionAsset.PAGES:
            yield from self.pages()

        elif asset == NotionAsset.DATABASES:
            yield from self.databases()

        elif asset == NotionAsset.USERS:
            yield from self.users()

        else:
            raise ValueError(f"This asset {asset} is unknown")
