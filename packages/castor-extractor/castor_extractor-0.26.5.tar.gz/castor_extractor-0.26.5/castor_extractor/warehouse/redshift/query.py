from ..abstract import (
    AbstractQueryBuilder,
    ExtractionQuery,
    TimeFilter,
    WarehouseAsset,
)
from .types import LongQuery

COMMON_CTE_PATH = "sql/long/common_cte.sql"
LONG_QUERY_PATHS: dict[LongQuery, str] = {
    LongQuery.METADATA: "sql/long/query_metadata.sql",
    LongQuery.PARTS: "sql/long/query_parts.sql",
}


class RedshiftQueryBuilder(AbstractQueryBuilder):
    """
    Builds queries to extract assets from Redshift.
    """

    def __init__(
        self,
        is_serverless: bool = False,
        time_filter: TimeFilter | None = None,
    ):
        super().__init__(time_filter=time_filter)
        self.is_serverless = is_serverless

    def build_custom_query(self, query_file: str) -> ExtractionQuery:
        """
        Build custom queries to extract redshift metadata that does not directly
        translate to typical assets (typical asset = database, schema, user...)
        """
        statement = self._load_from_file(query_file)
        params = self._time_filter.to_dict()
        return ExtractionQuery(statement, params)

    def build_long_query(self, long_query_type: LongQuery) -> ExtractionQuery:
        common_cte = self._load_from_file(COMMON_CTE_PATH)
        specific = self._load_from_file(LONG_QUERY_PATHS[long_query_type])
        statement = "\n".join([common_cte, specific])
        params = self._time_filter.to_dict()
        return ExtractionQuery(statement, params)

    def build(self, asset: WarehouseAsset) -> list[ExtractionQuery]:
        if asset == WarehouseAsset.QUERY and self.is_serverless:
            # To get the query history in Redshift Serverless, we cannot use STL tables
            query = self.build_custom_query("sql_serverless/query.sql")
        elif asset == WarehouseAsset.QUERY:
            # the default build expects `query.sql` one level higher
            query = self.build_custom_query("sql/short/query.sql")
        else:
            query = self.build_default(asset)
        return [query]
