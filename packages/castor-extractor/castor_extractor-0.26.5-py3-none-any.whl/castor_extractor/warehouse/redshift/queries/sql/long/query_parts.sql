,read_query AS (
    SELECT
        q.query::VARCHAR(256) AS query_id,
        q.text,
        q.sequence,
        q.sequence_count
    FROM query AS q
    INNER JOIN long_queries AS lq
        ON q.query = lq.query_id
)
,ddl_query AS (
    SELECT
        q.xid,
        q.text,
        q.sequence,
        COUNT(1) OVER(PARTITION BY q.xid) AS sequence_count
    FROM pg_catalog.stl_ddltext AS q
    INNER JOIN long_ddl AS ld
        ON q.xid = ld.query_id
    GROUP BY q.xid, q.text, q.sequence
)
,merged AS (
    SELECT
        rq.query_id,
        rq.text,
        rq.sequence,
        rq.sequence_count
    FROM read_query AS rq
    UNION DISTINCT
    SELECT
        -- force difference between ddl and read query query_id by artificially suffixing with `-ddl`
        -- so that query id (integer) will be guaranteed to be different from ddl xid (integer) + the suffix
        (dq.xid || '-ddl')::VARCHAR(256) AS query_id,
        dq.text,
        dq.sequence,
        dq.sequence_count
     FROM ddl_query AS dq
)

SELECT
    query_id,
    text,
    sequence,
    sequence_count
FROM merged
