WITH access_history AS (
  SELECT ah.*
  FROM snowflake.account_usage.access_history ah
  INNER JOIN snowflake.account_usage.query_history qh
    ON ah.query_id = qh.query_id
  WHERE TRUE
    AND DATE(CONVERT_TIMEZONE('UTC', query_start_time)) = :day
    AND HOUR(CONVERT_TIMEZONE('UTC', query_start_time)) BETWEEN :hour_min AND :hour_max
    AND {query_blocked}
),
access_enhanced AS (
  SELECT
    access_history.query_id,
    access_history.query_start_time,
    direct_sources.value: "objectName" AS source_object_name,
    direct_sources.value: "columnName" AS source_column_name,
    object_modified.value: "objectName" AS target_object_name,
    columns_modified.value: "columnName" AS target_column_name
  FROM
    access_history,
    LATERAL FLATTEN(INPUT => access_history.objects_modified) object_modified,
    LATERAL FLATTEN(INPUT => object_modified.value: "columns", OUTER => TRUE) columns_modified,
    LATERAL FLATTEN(INPUT => columns_modified.value: "directSources", OUTER => TRUE) direct_sources
)
SELECT
  query_id,
  CONCAT_WS('.', source_object_name, source_column_name) AS source_column_key,
  CONCAT_WS('.', target_object_name, target_column_name) AS target_column_key
FROM access_enhanced
WHERE TRUE
  AND source_column_key IS NOT NULL
  AND target_column_key IS NOT NULL
