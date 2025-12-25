from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from ...utils import (
    FetchNextPageBy,
    PaginationModel,
)

LIMIT_RECORDS_PER_PAGE = 2000


class SalesforcePagination(PaginationModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
    fetch_by: FetchNextPageBy = FetchNextPageBy.URL
    records: list
    next_records_url: str | None = None

    def is_last(self) -> bool:
        no_next_page = not self.next_records_url
        page_incomplete = len(self.records) < LIMIT_RECORDS_PER_PAGE
        return no_next_page or page_incomplete

    def next_page_payload(self) -> str | None:
        return self.next_records_url

    def page_results(self) -> list:
        return self.records
