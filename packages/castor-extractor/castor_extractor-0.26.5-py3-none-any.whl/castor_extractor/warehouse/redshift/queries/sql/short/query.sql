WITH parameters AS (
    SELECT
        :day AS day_start,
        :hour_min AS hour_min,
        :hour_max AS hour_max
),

queries_deduplicated AS (
    SELECT DISTINCT q.query
    FROM pg_catalog.stl_query AS q
        CROSS JOIN parameters AS p
    WHERE TRUE
        AND DATE(q.starttime) = p.day_start
        AND EXTRACT('hour' FROM q.starttime) BETWEEN p.hour_min AND p.hour_max
),

query AS (
    SELECT
        q.query,
        qt.text,
        qt.sequence,
        COUNT(*) OVER(PARTITION BY q.query) AS sequence_count
    FROM queries_deduplicated AS q
        INNER JOIN pg_catalog.stl_querytext AS qt ON q.query = qt.query
),

raw_query_text AS
(
    SELECT
        q.query,
        LISTAGG(q.text, '') WITHIN GROUP (ORDER BY q.sequence) AS agg_text
    FROM query AS q
    WHERE TRUE
    -- LISTAGG raises an error when total length >= 65535
    -- each sequence contains 200 char max
        AND q.sequence_count < (65535 / 200)
    GROUP BY q.query
),

query_text AS (
    SELECT
        query,
        CASE
            WHEN agg_text ILIKE 'INSERT INTO%%'
                THEN REGEXP_REPLACE(agg_text, 'VALUES (.*)', 'DEFAULT VALUES')
            ELSE agg_text
        END AS agg_text
    FROM raw_query_text
),

read_query AS (
    SELECT
        q.query::VARCHAR(256) AS query_id,
        qt.agg_text::VARCHAR(60000) AS query_text,
        db.oid AS database_id,
        q.database AS database_name,
        q.pid AS process_id,
        q.aborted,
        q.starttime AS start_time,
        q.endtime AS end_time,
        q.userid AS user_id,
        q.label
    FROM pg_catalog.stl_query AS q
        JOIN query_text AS qt ON q.query = qt.query
        JOIN pg_catalog.pg_database AS db ON db.datname = q.database
        CROSS JOIN parameters AS p
    WHERE TRUE
        AND DATE(q.starttime) = p.day_start
        AND EXTRACT('hour' FROM q.starttime) BETWEEN p.hour_min AND p.hour_max
),

-- the DDL part is sensible to any change of JOIN and AGGREGATION: test in the field prior to merging
ddl_query AS (
    SELECT
        (q.xid || '-' || q.query_part_rank)::VARCHAR(256) AS query_id,
        q.query_text::VARCHAR(20000) AS query_text,
        db.oid AS database_id,
        db.datname AS database_name,
        q.process_id,
        0 AS aborted,
        q.start_time,
        q.end_time,
        q.user_id,
        q.label
    FROM (
        SELECT
            q.userid AS user_id,
            q.pid AS process_id,
            q.xid,
            q.starttime AS start_time,
            MAX(q.endtime) AS end_time,
            MIN(q.label) AS "label",
            (LISTAGG(q.text, '') WITHIN GROUP (ORDER BY q.sequence)) AS query_text,
            RANK() OVER(PARTITION BY q.userid, q.pid, q.xid ORDER BY q.starttime) AS query_part_rank
        FROM pg_catalog.stl_ddltext AS q
            CROSS JOIN parameters AS p
        WHERE TRUE
            AND DATE(q.starttime) = p.day_start
            AND EXTRACT('hour' FROM q.starttime) BETWEEN p.hour_min AND p.hour_max
            -- LISTAGG raises an error when total length >= 64K
            AND q.sequence < (65535 / 200)
        GROUP BY q.userid, q.pid, q.xid, q.starttime
    ) AS q
    CROSS JOIN pg_catalog.pg_database AS db
    WHERE db.datname = CURRENT_DATABASE()
),

merged AS (
    SELECT * FROM read_query

    UNION DISTINCT

    SELECT * FROM ddl_query
)

SELECT
    q.*,
    u.usename AS user_name
FROM merged AS q
    JOIN pg_catalog.pg_user AS u ON u.usesysid = q.user_id
