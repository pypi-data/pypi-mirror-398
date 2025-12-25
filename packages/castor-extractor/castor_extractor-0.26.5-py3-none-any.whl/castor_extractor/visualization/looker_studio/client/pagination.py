from pydantic import AliasChoices, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ....utils import PaginationModel

NEXT_PAGE_KEY = "pageToken"


class LookerStudioPagination(PaginationModel):
    items: list = Field(
        default_factory=list,
        validation_alias=AliasChoices("items", "users", "assets"),
    )
    next_page_token: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    def is_last(self) -> bool:
        return self.next_page_token is None

    def next_page_payload(self) -> dict:
        return {NEXT_PAGE_KEY: self.next_page_token}

    def page_results(self) -> list:
        return self.items
