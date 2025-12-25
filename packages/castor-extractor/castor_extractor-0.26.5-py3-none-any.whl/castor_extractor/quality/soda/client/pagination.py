from ....utils import PaginationModel

_CLOUD_FIRST_PAGE = 0


class SodaCloudPagination(PaginationModel):
    content: list[dict]
    last: bool

    def is_last(self) -> bool:
        return self.last

    def next_page_payload(self) -> dict:
        current_page = (
            self.current_page_payload[self.fetch_by.value]["page"]
            if self.current_page_payload
            else _CLOUD_FIRST_PAGE
        )
        return {"page": current_page + 1}

    def page_results(self) -> list:
        return self.content
