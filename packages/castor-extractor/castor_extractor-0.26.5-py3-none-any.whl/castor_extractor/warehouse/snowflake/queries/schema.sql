SELECT
    s.schema_id,
    s.schema_name,
    s.catalog_id AS database_id,
    s.catalog_name AS database_name,
    s.schema_owner,
    s.is_transient,
    s.comment,
    s.last_altered,
    s.created,
    s.deleted
FROM snowflake.account_usage.schemata AS s
WHERE TRUE
    AND UPPER(catalog_name) NOT IN ('SNOWFLAKE', 'UTIL_DB')
    AND (
        deleted IS NULL
        OR deleted > CURRENT_TIMESTAMP - INTERVAL '12 hours'
    )
    AND TRIM(COALESCE(schema_name, '')) != ''
    AND {database_allowed}
    AND {database_blocked}
    AND CASE {has_fetch_transient} WHEN FALSE THEN NOT s.is_transient::BOOLEAN ELSE TRUE END
QUALIFY ROW_NUMBER()
    OVER (
        PARTITION BY
            s.schema_id,
            s.catalog_id
        ORDER BY
            s.last_altered DESC
    ) = 1
