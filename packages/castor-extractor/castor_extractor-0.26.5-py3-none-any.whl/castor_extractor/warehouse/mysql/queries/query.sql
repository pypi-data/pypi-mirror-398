/*
  This query returns an empty table with the given columns.
  This allows us to ingest view DDL
 */
SELECT
    NULL AS query_id,
    NULL AS database_id,
    NULL AS database_name,
    NULL AS schema_name,
    NULL AS query_text,
    NULL AS user_id,
    NULL AS start_time,
    NULL AS end_time
WHERE FALSE
