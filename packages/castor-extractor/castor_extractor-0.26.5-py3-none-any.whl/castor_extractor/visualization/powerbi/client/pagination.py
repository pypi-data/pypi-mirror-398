from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel

from ....utils import (
    FetchNextPageBy,
    PaginationModel,
)


class PowerBIAPIPagination(PaginationModel):
    """Handles the pagination of Power BI REST API calls for activity events"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    fetch_by: FetchNextPageBy = FetchNextPageBy.URL

    activity_event_entities: list
    continuation_uri: str | None = None
    last_result_set: bool = False

    def is_last(self) -> bool:
        return self.last_result_set

    def next_page_payload(self) -> str | None:
        return self.continuation_uri

    def page_results(self) -> list:
        return self.activity_event_entities


class GraphAPIPagination(PaginationModel):
    """
    Handles the pagination of Graph API calls.
    The response is expected to be of the form:
    ```
    {
        "@odata.context":"<the URL that was called>",
        "@odata.nextLink":"<the URL to the next page>",
        "value":[
            {<info user 1>},
            {<info user 2>},
            {<info user 3>},
       ]
    }
    ```

    The "@odata.nextLink" key is optional.
    """

    fetch_by: FetchNextPageBy = FetchNextPageBy.URL

    value: list = Field(default_factory=list)
    next_url: str | None = Field(
        validation_alias="@odata.nextLink",
        default=None,
    )

    def is_last(self) -> bool:
        return self.next_url is None

    def next_page_payload(self) -> str | None:
        return self.next_url

    def page_results(self) -> list:
        return self.value
