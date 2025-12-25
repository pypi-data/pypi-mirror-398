from ....utils import PaginationModel


class CoalescePagination(PaginationModel):
    """
    Class to handle paginated results for Coalesce
    See their documentation here
    https://docs.coalesce.io/docs/api
    """

    data: list
    next: str | None | int | None = None

    def is_last(self) -> bool:
        """Stopping condition for the pagination"""
        return self.next is None

    def next_page_payload(self):
        """Payload enabling to generate the request for the next page"""
        return {"startingFrom": self.next}

    def page_results(self) -> list:
        """List of results of the current page"""
        return self.data
