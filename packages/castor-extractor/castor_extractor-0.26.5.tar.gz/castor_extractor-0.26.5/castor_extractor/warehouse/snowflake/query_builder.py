from ...utils import QueryFilter, values_to_params
from ..abstract import (
    CATALOG_ASSETS,
    AbstractQueryBuilder,
    ExtractionQuery,
    TimeFilter,
    WarehouseAsset,
)

DB_FILTERED_ASSETS = (
    *CATALOG_ASSETS,
    WarehouseAsset.VIEW_DDL,
)
QUERY_FILTERED_ASSETS = (
    WarehouseAsset.COLUMN_LINEAGE,
    WarehouseAsset.QUERY,
)


def _transient_filter(has_transient: bool | None = False) -> QueryFilter:
    """
    Build a filter controlling whether transient Snowflake objects
    should be fetched.

    The filter replaces the `{has_fetch_transient}` placeholder with either
    `TRUE` or `FALSE`, allowing queries to include or exclude transient objects
    (e.g., transient tables or schemas).
    """
    return QueryFilter(
        placeholder="has_fetch_transient",
        expression="TRUE" if has_transient else "FALSE",
    )


def _database_filter(db_list: list[str] | None, allow: bool) -> QueryFilter:
    """
    Build a filter restricting results based on allowed or blocked databases.

    This filter replaces either the {database_allowed} or {database_blocked}
    placeholder in a query. It generates an IN or NOT IN clause
    with parameterized database names.
    """
    placeholder = "database_allowed" if allow else "database_blocked"
    if not db_list:
        # replace the placeholder with dummy 'True' when list is empty
        return QueryFilter(placeholder, expression="TRUE")
    operator = "IN" if allow else "NOT IN"
    params = values_to_params(prefix=placeholder, values=db_list)
    db_params_formatted = ", ".join(f":{key}" for key in params)
    return QueryFilter(
        placeholder=placeholder,
        expression=f"database_name {operator} ({db_params_formatted})",
        params=params,
    )


def _query_blocked_filter(query_blocked: list[str] | None) -> QueryFilter:
    """
    Build a filter that excludes SQL queries matching specified blocked patterns

    This filter replaces the {query_blocked} placeholder with one
    or more "NOT ILIKE" conditions.

    The values argument is a list of case-insensitive string patterns
    to exclude from query text. SQL wildcards are supported: % and _"
    """
    placeholder = "query_blocked"
    if not query_blocked:
        # replace the placeholder with dummy 'True' when list is empty
        return QueryFilter(placeholder, expression="TRUE")
    params = values_to_params(prefix=placeholder, values=query_blocked)
    expression = " AND ".join(f"query_text NOT ILIKE :{key}" for key in params)
    return QueryFilter(
        placeholder=placeholder,
        expression=f"({expression})",
        params=params,
    )


class SnowflakeQueryBuilder(AbstractQueryBuilder):
    """
    Builds queries to extract assets from Snowflake.
    """

    def __init__(
        self,
        time_filter: TimeFilter | None = None,
        db_allowed: list[str] | None = None,
        db_blocked: list[str] | None = None,
        query_blocked: list[str] | None = None,
        fetch_transient: bool | None = False,
    ):
        super().__init__(time_filter=time_filter)
        self._db_allowed = _database_filter(db_allowed, allow=True)
        self._db_blocked = _database_filter(db_blocked, allow=False)
        self._query_blocked = _query_blocked_filter(query_blocked)
        self._transient = _transient_filter(fetch_transient)

    def build(self, asset: WarehouseAsset) -> list[ExtractionQuery]:
        query = self.build_default(asset)

        filters: list[QueryFilter] = []
        if asset in DB_FILTERED_ASSETS:
            filters.append(self._db_allowed)
            filters.append(self._db_blocked)
            filters.append(self._transient)
        if asset in QUERY_FILTERED_ASSETS:
            filters.append(self._query_blocked)

        query.apply_filters(filters)
        return [query]
