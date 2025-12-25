from ..abstract import (
    AbstractQueryBuilder,
    ExtractionQuery,
    TimeFilter,
    WarehouseAsset,
)


class MySQLQueryBuilder(AbstractQueryBuilder):
    """
    Builds queries to extract assets from MySQL.
    """

    def __init__(
        self,
        time_filter: TimeFilter | None = None,
    ):
        super().__init__(time_filter=time_filter)

    def build(self, asset: WarehouseAsset) -> list[ExtractionQuery]:
        query = self.build_default(asset)
        return [query]
