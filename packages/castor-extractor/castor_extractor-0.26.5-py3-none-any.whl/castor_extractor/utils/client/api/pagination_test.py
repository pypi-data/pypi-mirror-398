from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from .pagination import PaginationModel, fetch_all_pages


class _TestPagination(PaginationModel):
    next_page: str | None = None
    entries: list = Field(default_factory=list)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    def is_last(self) -> bool:
        return self.next_page is None

    def next_page_payload(self) -> dict:
        return {"page": self.next_page}

    def page_results(self) -> list:
        return self.entries


def _request(pagination_params: dict | None = None):
    if not pagination_params:
        return {
            "nextPage": "next_page_id",
            "entries": [1, 2, 3, 4, 5],
        }
    if pagination_params.get("page") == "next_page_id":
        return {
            "nextPage": "next_page_id_2",
            "entries": [6, 7, 8, 9, 10],
        }
    if pagination_params.get("page") == "next_page_id_2":
        return {
            "nextPage": None,
            "entries": [11],
        }

    raise AssertionError(f"call has unexpected parameters: {pagination_params}")


def test__TestPagination():
    all_results = fetch_all_pages(_request, _TestPagination)
    assert list(all_results) == [i for i in range(1, 12)]
