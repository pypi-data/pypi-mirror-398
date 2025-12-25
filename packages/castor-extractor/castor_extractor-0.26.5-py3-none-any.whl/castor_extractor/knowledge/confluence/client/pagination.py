from pydantic import AliasPath, Field

from ....utils import (
    FetchNextPageBy,
    PaginationModel,
)


class ConfluencePagination(PaginationModel):
    """Class to handle paginated results for confluence"""

    fetch_by: FetchNextPageBy = FetchNextPageBy.URL

    results: list = Field(default_factory=list)
    next_url: str | None = Field(
        validation_alias=AliasPath("_links", "next"),
        default=None,
    )

    def is_last(self) -> bool:
        """Stopping condition for the pagination"""
        return self.next_url is None

    def next_page_payload(self) -> str | None:
        """Payload enabling to generate the request for the next page"""
        return self.next_url

    def page_results(self) -> list:
        """List of results of the current page"""
        return self.results
