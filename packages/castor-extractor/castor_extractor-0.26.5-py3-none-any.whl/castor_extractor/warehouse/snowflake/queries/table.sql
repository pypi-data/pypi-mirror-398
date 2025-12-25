WITH
table_tags AS (
    SELECT
        tr.object_id AS table_id,
        CONCAT(tr.tag_name, ':', tr.tag_value) AS tag,
        tr.tag_name,
        tr.tag_value
    FROM snowflake.account_usage.tag_references tr
    WHERE TRUE
        AND tr.domain = 'TABLE'
),

tags_agg_tables AS (
    SELECT
        t.table_id,
        ARRAY_AGG(tt.tag)
            WITHIN GROUP (ORDER BY tt.tag_name, tt.tag_value) tags
  FROM snowflake.account_usage.tables t
  LEFT JOIN table_tags tt ON t.table_id = tt.table_id
  GROUP BY t.table_id
)

SELECT
    t.table_id,
    t.table_name,
    t.table_schema_id AS schema_id,
    t.table_schema AS "schema_name",
    t.table_catalog_id AS database_id,
    t.table_catalog AS database_name,
    t.table_owner,
    t.table_type,
    t.is_transient,
    t.row_count,
    t.bytes,
    t.comment,
    t.created,
    t.last_altered,
    t.deleted,
    ta.tags,
    t.is_dynamic
FROM snowflake.account_usage.tables AS t
    JOIN snowflake.account_usage.schemata AS s ON s.schema_id = t.table_schema_id
    JOIN tags_agg_tables ta ON t.table_id = ta.table_id
WHERE TRUE
    AND TRIM(COALESCE(t.table_name, '')) != ''
    AND TRIM(COALESCE(s.schema_name, '')) != ''
    AND UPPER(t.table_catalog) NOT IN ('SNOWFLAKE', 'UTIL_DB')
    AND (
        t.deleted IS NULL
        OR t.deleted > CURRENT_TIMESTAMP - INTERVAL '12 hours'
    )
    AND {database_allowed}
    AND {database_blocked}
    AND CASE {has_fetch_transient} WHEN FALSE THEN NOT t.is_transient::BOOLEAN ELSE TRUE END
