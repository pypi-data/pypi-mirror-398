/*
    - queries_deduplicated: distrinct query ids in the timeframe we are interested in
    - query: contains all query fragments
    - long queries: ids of queries that are too long to be reconstructed using the function LISTAGG
    - long ddl: ids of ddl that are too long to be reconstructed using the function LISTAGG
*/
WITH parameters AS (
    SELECT
        :day AS day_start,
        :hour_min AS hour_min,
        :hour_max AS hour_max,
        (65535 / 200) AS max_sequence_count
)
,queries_deduplicated AS (
    SELECT DISTINCT q.query
    FROM pg_catalog.stl_query AS q
        CROSS JOIN parameters AS p
    WHERE TRUE
        AND DATE(q.starttime) = p.day_start
        AND EXTRACT('hour' FROM q.starttime) BETWEEN p.hour_min AND p.hour_max
)
,query AS (
    SELECT
        q.query,
        qt.text,
        qt.sequence,
        COUNT(1) OVER(PARTITION BY q.query) AS sequence_count
    FROM queries_deduplicated AS q
        INNER JOIN pg_catalog.stl_querytext AS qt ON q.query = qt.query
)
,long_queries AS
(
    SELECT DISTINCT q.query AS query_id
    FROM query AS q
        CROSS JOIN parameters AS p
    WHERE TRUE
        AND q.sequence_count > p.max_sequence_count
)
,long_ddl AS (
    SELECT DISTINCT q.xid AS query_id
    FROM pg_catalog.stl_ddltext AS q
        CROSS JOIN parameters AS p
    WHERE TRUE
        AND DATE(q.starttime) = p.day_start
        AND EXTRACT('hour' FROM q.starttime) BETWEEN p.hour_min AND p.hour_max
        AND q.sequence > p.max_sequence_count
)
