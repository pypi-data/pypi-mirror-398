SELECT
    q.query_id,
    qt.query_sql_text as query_text,
    rs.count_executions,
    rs.last_duration as duration,
    rs.last_execution_time as start_time,
    'unknown-user' as user_name,
    'unknown-user' as user_id,
    DATEADD(SECOND, last_duration / 1000000,
        DATEADD(MICROSECOND, last_duration % 1000000, rs.last_execution_time)
    ) AS end_time
FROM
    [{database}].sys.query_store_runtime_stats AS rs
INNER JOIN
    [{database}].sys.query_store_plan p
    ON rs.plan_id = p.plan_id
INNER JOIN
    [{database}].sys.query_store_query q
    ON p.query_id = q.query_id
INNER JOIN
    [{database}].sys.query_store_query_text qt
    ON q.query_text_id = qt.query_text_id
WHERE
    CAST(rs.last_execution_time AS DATE) = :day
    AND DATEPART(HOUR, rs.last_execution_time) BETWEEN :hour_min AND :hour_max
