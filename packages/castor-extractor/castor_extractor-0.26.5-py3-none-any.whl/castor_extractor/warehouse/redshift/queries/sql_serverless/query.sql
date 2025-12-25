WITH parameters AS (
    SELECT
        :day AS day_start,
        :hour_min AS hour_min,
        :hour_max AS hour_max
),

queries_deduplicated AS (
    SELECT DISTINCT q.query_id
    FROM SYS_QUERY_HISTORY AS q
        CROSS JOIN parameters AS p
    WHERE TRUE
        AND DATE(q.start_time) = p.day_start
        AND EXTRACT('hour' FROM q.start_time) BETWEEN p.hour_min AND p.hour_max
),

query AS (
    SELECT
        q.query_id,
        qt.text,
        qt.sequence,
        COUNT(*) OVER(PARTITION BY q.query_id) AS sequence_count
    FROM queries_deduplicated AS q
        INNER JOIN SYS_QUERY_TEXT AS qt ON q.query_id = qt.query_id
),

raw_query_text AS
(
    SELECT
        q.query_id,
        LISTAGG(q.text, '') WITHIN GROUP (ORDER BY q.sequence) AS agg_text
    FROM query AS q
    WHERE TRUE
    -- LISTAGG raises an error when total length >= 65535
    -- each query text contains 4000 char max
        AND q.sequence_count < (65535 / 4000)
    GROUP BY q.query_id
),

query_text AS (
    SELECT
        query_id,
        CASE
            WHEN agg_text ILIKE 'INSERT INTO%%'
                THEN REGEXP_REPLACE(agg_text, 'VALUES (.*)', 'DEFAULT VALUES')
            ELSE agg_text
        END AS agg_text
    FROM raw_query_text
)
SELECT
    q.query_id::VARCHAR(256) AS query_id,
    qt.agg_text::VARCHAR(60000) AS query_text,
    q.database_name AS database_id,
    q.database_name AS database_name,
    q.session_id AS process_id,
    0 as aborted,
    q.start_time AS start_time,
    q.end_time AS end_time,
    q.user_id AS user_id,
    q.query_label,
    u.usename AS user_name
FROM SYS_QUERY_HISTORY AS q
    JOIN query_text AS qt ON q.query_id = qt.query_id
    JOIN pg_catalog.pg_user AS u ON u.usesysid = q.user_id
    CROSS JOIN parameters AS p
WHERE TRUE
    AND DATE(q.start_time) = p.day_start
    AND EXTRACT('hour' FROM q.start_time) BETWEEN p.hour_min AND p.hour_max
    AND q.status = 'success'
