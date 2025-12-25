from datetime import datetime

from ..abstract import TimeFilter, WarehouseAsset
from .query_builder import SnowflakeQueryBuilder


def test_snowflake_query_builder():
    day = datetime(1969, 7, 20)
    time_filter = TimeFilter(day=day, hour_min=20, hour_max=21)

    # Step 1 - empty filters
    builder = SnowflakeQueryBuilder(
        time_filter=time_filter,
        db_allowed=None,
        db_blocked=None,
        query_blocked=None,
    )
    query = builder.build(WarehouseAsset.QUERY)[0]
    assert len(query.params) == 3  # day, hour_min, hour_max
    assert "{query_blocked}" not in query.statement
    assert query.statement.count("AND TRUE") == 1

    query = builder.build(WarehouseAsset.SCHEMA)[0]
    assert len(query.params) == 0
    assert "{db_allowed}" not in query.statement
    assert "{db_blocked}" not in query.statement
    assert query.statement.count("AND TRUE") == 2

    # Step 2 - filters
    builder = SnowflakeQueryBuilder(
        time_filter=time_filter,
        db_allowed=["foo", "bar"],
        db_blocked=None,
        query_blocked=["SHOW DATABASES", "SELECT 1 FROM %"],
    )
    query = builder.build(WarehouseAsset.QUERY)[0]
    assert len(query.params) == 5  # 3 time filters + 2 query filters
    assert "{query_blocked}" not in query.statement
    assert query.params["query_blocked_0"] == "SHOW DATABASES"
    assert query.params["query_blocked_1"] == "SELECT 1 FROM %"
    expected_chunk = "query_text NOT ILIKE :query_blocked"
    assert f"AND ({expected_chunk}_0 AND {expected_chunk}_1)" in query.statement

    query = builder.build(WarehouseAsset.SCHEMA)[0]
    assert len(query.params) == 2  # 2 database filters
    assert "{database_allowed}" not in query.statement
    assert "{database_blocked}" not in query.statement
    assert query.params["database_allowed_0"] == "foo"
    assert query.params["database_allowed_1"] == "bar"
    expected = "database_name IN (:database_allowed_0, :database_allowed_1)"
    assert expected in query.statement
