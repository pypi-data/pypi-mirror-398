from pydantic import Field

from ....utils import PaginationModel


class NotionPagination(PaginationModel):
    """Class to handle paginated results"""

    results: list = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False

    def is_last(self) -> bool:
        return not self.has_more

    def next_page_payload(self) -> dict:
        return {"start_cursor": self.next_cursor}

    def page_results(self) -> list:
        return self.results
