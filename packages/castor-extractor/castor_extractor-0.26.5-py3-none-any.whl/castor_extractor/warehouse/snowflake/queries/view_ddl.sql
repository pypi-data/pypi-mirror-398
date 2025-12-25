SELECT
    v.table_id,
    v.table_name,
    v.table_schema_id AS schema_id,
    v.table_schema AS "schema_name",
    v.table_catalog_id AS database_id,
    v.table_catalog AS database_name,
    v.table_owner,
    v.view_definition
FROM
    snowflake.account_usage.views AS v
    JOIN snowflake.account_usage.schemata AS s ON s.schema_id = v.table_schema_id
WHERE TRUE
    AND UPPER(v.table_catalog) NOT IN ('SNOWFLAKE', 'UTIL_DB')
    AND (
        v.deleted IS NULL
        OR v.deleted > CURRENT_TIMESTAMP - INTERVAL '12 hours'
    )
    AND {database_allowed}
    AND {database_blocked}
    AND CASE {has_fetch_transient} WHEN FALSE THEN NOT s.is_transient::BOOLEAN ELSE TRUE END
