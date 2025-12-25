from pydantic import Field

from ...utils import PaginationModel

DATABRICKS_PAGE_SIZE = 100


class DatabricksPagination(PaginationModel):
    next_page_token: str | None = None
    has_next_page: bool = False
    res: list[dict] = Field(default_factory=list)

    def is_last(self) -> bool:
        return not (self.has_next_page and self.next_page_token)

    def next_page_payload(self) -> dict:
        return {"page_token": self.next_page_token}

    def page_results(self) -> list:
        return self.res
