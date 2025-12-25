,query_metadata AS (
    SELECT
        q.query::VARCHAR(256) AS query_id,
        db.oid AS database_id,
        q.database AS database_name,
        q.pid AS process_id,
        q.aborted,
        q.starttime AS start_time,
        q.endtime AS end_time,
        q.userid AS user_id,
        q.label
    FROM pg_catalog.stl_query AS q
        JOIN pg_catalog.pg_database AS db ON db.datname = q.database
        JOIN long_queries AS lq ON lq.query_id = q.query
        CROSS JOIN parameters AS p
    WHERE TRUE
        AND DATE(q.starttime) = p.day_start
        AND EXTRACT('hour' FROM q.starttime) BETWEEN p.hour_min AND p.hour_max
)
,all_long_ddl AS (
    SELECT
        q.userid AS user_id,
        q.pid AS process_id,
        q.xid,
        q.starttime AS start_time,
        MAX(q.endtime) AS end_time,
        MIN(q.label) AS "label"
    FROM pg_catalog.stl_ddltext AS q
        JOIN long_ddl AS ld ON ld.query_id = q.xid
    GROUP BY q.userid, q.pid, q.xid, q.starttime
)
,ddl_metadata AS (
    SELECT
        (q.xid || '-ddl')::VARCHAR(256) AS query_id,
        db.oid AS database_id,
        db.datname AS database_name,
        q.process_id,
        0 AS aborted,
        q.start_time,
        q.end_time,
        q.user_id,
        q.label
    FROM all_long_ddl AS q
        CROSS JOIN pg_catalog.pg_database AS db
    WHERE db.datname = CURRENT_DATABASE()
)
,merged AS (
    SELECT
        aborted,
        database_id,
        database_name,
        end_time,
        label,
        process_id,
        query_id,
        start_time,
        user_id
    FROM query_metadata AS qm
    UNION DISTINCT
    SELECT
        aborted,
        database_id,
        database_name,
        end_time,
        label,
        process_id,
        query_id,
        start_time,
        user_id
     FROM ddl_metadata AS dm
)

SELECT
    q.aborted,
    q.database_id,
    q.database_name,
    q.end_time,
    q.label,
    q.process_id,
    q.query_id,
    q.start_time,
    q.user_id,
    u.usename AS user_name
FROM merged AS q
    JOIN pg_catalog.pg_user AS u ON u.usesysid = q.user_id
