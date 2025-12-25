from ...utils import PaginationModel
from ...utils.salesforce.pagination import LIMIT_RECORDS_PER_PAGE
from .soql import (
    SOBJECTS_QUERY_TPL,
)

# Implicit (hard-coded in Salesforce) limitation when using SOQL of 2,000 rows
FIRST_START_DURABLE_ID = "0000"


def format_sobject_query(
    start_durable_id: str = FIRST_START_DURABLE_ID,
) -> str:
    return SOBJECTS_QUERY_TPL.format(
        start_durable_id=start_durable_id,
        limit=LIMIT_RECORDS_PER_PAGE,
    )


class SalesforceSQLPagination(PaginationModel):
    records: list

    def next_page_payload(self) -> dict | None:
        start_durable_id = self.records[-1]["DurableId"]
        query = format_sobject_query(start_durable_id)
        return {"q": query}

    def is_last(self) -> bool:
        return len(self.records) < LIMIT_RECORDS_PER_PAGE

    def page_results(self) -> list:
        return self.records
