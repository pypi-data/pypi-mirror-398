from pydantic import ConfigDict, Field

from ....utils import PaginationModel

METADATA_BATCH_SIZE = 100


class ThoughtSpotPagination(PaginationModel):
    data_rows: list = Field(default_factory=list)
    record_offset: int
    record_size: int

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    def is_last(self) -> bool:
        return len(self.data_rows) < METADATA_BATCH_SIZE

    def next_page_payload(self) -> dict:
        return {"record_offset": self.record_offset + METADATA_BATCH_SIZE}

    def page_results(self) -> list:
        return self.data_rows
