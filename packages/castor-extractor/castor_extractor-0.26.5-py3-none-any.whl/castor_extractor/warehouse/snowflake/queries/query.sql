/*
    Extracts successful user-executed SQL queries from Snowflake’s ACCOUNT_USAGE.QUERY_HISTORY
    for a given day and hour range.

    Filters out system, maintenance, and trivial queries (e.g. SELECT 1, SHOW, USE, etc.),
    and cleans INSERT statements by replacing explicit VALUES with DEFAULT VALUES.

    Performs early deduplication using query_hash and user_name to keep only one query-run
    per user, reducing redundant data while preserving user activity accuracy.
*/
WITH queries AS
(
    SELECT
        query_id,
        -- dropping INSERT values
        IFF(
            query_type = 'INSERT',
            REGEXP_REPLACE(query_text, 'VALUES (.*)', 'DEFAULT VALUES'),
            query_text
        ) AS query_text,
        database_id,
        database_name,
        schema_id,
        schema_name,
        query_type,
        session_id,
        user_name,
        user_name as user_id,
        role_name,
        warehouse_id,
        warehouse_name,
        warehouse_size,
        execution_status,
        error_code,
        error_message,
        CONVERT_TIMEZONE('UTC', start_time) AS start_time,
        CONVERT_TIMEZONE('UTC', end_time) AS end_time,
        total_elapsed_time,
        bytes_scanned,
        percentage_scanned_from_cache,
        bytes_written,
        bytes_written_to_result,
        bytes_read_from_result,
        rows_produced,
        rows_inserted,
        rows_updated,
        rows_deleted,
        rows_unloaded,
        bytes_deleted,
        partitions_scanned,
        partitions_total,
        compilation_time,
        execution_time,
        queued_provisioning_time,
        queued_repair_time,
        queued_overload_time,
        transaction_blocked_time,
        release_version,
        is_client_generated_statement,
        -- keep one query-run per user to preserve the calculation of frequent users
        ROW_NUMBER() OVER (PARTITION BY hash(query_hash, user_name) ORDER BY start_time DESC) AS query_rank
    FROM
        snowflake.account_usage.query_history
    WHERE TRUE
        AND DATE(CONVERT_TIMEZONE('UTC', start_time)) = :day
        AND HOUR(CONVERT_TIMEZONE('UTC', start_time)) BETWEEN :hour_min AND :hour_max
        AND execution_status = 'SUCCESS'
        AND query_text != 'SELECT 1'
        AND {query_blocked}
        AND TRIM(COALESCE(query_text, '')) != ''
        AND query_type NOT IN (
            'ALTER_SESSION',
            'BEGIN_TRANSACTION',
            'CALL',
            'COMMENT',
            'COMMIT',
            'CREATE',
            'DESCRIBE',
            'DROP',
            'EXPLAIN',
            'GET_FILES',
            'GRANT',
            'PUT_FILES',
            'REFRESH_DYNAMIC_TABLE_AT_REFRESH_VERSION',
            'REMOVE_FILES',
            'REVOKE',
            'ROLLBACK',
            'SET',
            'SHOW',
            'TRUNCATE_TABLE',
            'UNDROP',
            'UNLOAD',
            'USE'
        )
)
SELECT
    *
FROM
    queries
WHERE
    -- remove duplicates at extraction time saves processing time and storage space
    query_rank = 1
