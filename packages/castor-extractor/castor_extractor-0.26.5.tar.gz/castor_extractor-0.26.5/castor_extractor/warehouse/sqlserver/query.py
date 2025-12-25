import logging

from ..abstract import (
    AbstractQueryBuilder,
    ExtractionQuery,
    TimeFilter,
    WarehouseAsset,
)

logger = logging.getLogger(__name__)


_NO_DATABASE_ERROR_MSG = (
    "No databases eligible for extraction. "
    "If you are using the db_allow/db_block options, please make sure to use the correct case."
)

_SQLSERVER_DUPLICATED_ASSETS: tuple[WarehouseAsset, ...] = (
    WarehouseAsset.USER,
)


class MSSQLQueryBuilder(AbstractQueryBuilder):
    """
    Builds queries to extract assets from SQL Server.
    """

    def __init__(
        self,
        databases: list[str],
        time_filter: TimeFilter | None = None,
    ):
        super().__init__(
            time_filter=time_filter,
            duplicated=_SQLSERVER_DUPLICATED_ASSETS,
        )
        if not databases:
            raise ValueError(_NO_DATABASE_ERROR_MSG)
        self._databases = databases

    @staticmethod
    def _format(
        query: ExtractionQuery,
        database: str,
    ) -> ExtractionQuery:
        return ExtractionQuery(
            statement=query.statement.format(database=database),
            params=query.params,
            database=database,
        )

    def build(self, asset: WarehouseAsset) -> list[ExtractionQuery]:
        query = self.build_default(asset)

        if asset == WarehouseAsset.DATABASE:
            # database.sql does not include a {database} placeholder.
            # Indeed, databases are extracted at the server level
            # (not scoped to a specific database).
            return [query]

        logger.info(
            f"\tWill run queries with following database params: {self._databases}",
        )
        return [self._format(query, database) for database in self._databases]
