SELECT
    database_id,
    database_name,
    database_owner,
    is_transient,
    comment,
    last_altered,
    created,
    deleted
FROM snowflake.account_usage.databases
WHERE TRUE
    AND UPPER(database_name) NOT IN ('SNOWFLAKE', 'UTIL_DB')
    AND UPPER(database_name) NOT LIKE 'USER$%'  -- ignore private notebooks
    AND (
        deleted IS NULL
        OR deleted > CURRENT_TIMESTAMP - INTERVAL '12 hours'
    )
    AND {database_allowed}
    AND {database_blocked}
    AND CASE {has_fetch_transient} WHEN FALSE THEN NOT is_transient::BOOLEAN ELSE TRUE END
