WITH column_tags AS (
    SELECT
        -- contrary to table tags, joining with object_id does not work well
        tr.column_id,
        CONCAT(tr.tag_name, ':', tr.tag_value) AS tag,
        tr.tag_name,
        tr.tag_value
    FROM snowflake.account_usage.tag_references tr
    WHERE TRUE
        AND tr.domain = 'COLUMN'
),
tags_agg_columns AS (
    SELECT
        c.column_id,
        ARRAY_AGG(ct.tag)
            WITHIN GROUP (ORDER BY ct.tag_name, ct.tag_value) tags
  FROM snowflake.account_usage.columns c
  LEFT JOIN column_tags ct ON c.column_id = ct.column_id
  GROUP BY c.column_id
)
SELECT
    c.column_id,
    c.column_name,
    c.table_id,
    c.table_name,
    c.table_schema_id AS schema_id,
    c.table_schema AS "schema_name",
    c.table_catalog_id AS database_id,
    c.table_catalog AS database_name,
    c.ordinal_position,
    c.is_nullable,
    c.data_type,
    c.maximum_cardinality,
    c.character_maximum_length,
    c.character_octet_length,
    c.numeric_precision,
    c.numeric_precision_radix,
    c.numeric_scale,
    c.datetime_precision,
    c.interval_type,
    c.interval_precision,
    c.comment,
    c.deleted,
    ta.tags
FROM snowflake.account_usage.columns AS c
    JOIN snowflake.account_usage.schemata AS s ON s.schema_id = c.table_schema_id
    JOIN snowflake.account_usage.tables AS t ON t.table_id = c.table_id
    JOIN tags_agg_columns ta ON c.column_id = ta.column_id
WHERE TRUE
    AND TRIM(COALESCE(c.column_name, '')) != ''
    AND TRIM(COALESCE(t.table_name, '')) != ''
    AND TRIM(COALESCE(s.schema_name, '')) != ''
    AND UPPER(c.table_catalog) NOT IN ('SNOWFLAKE', 'UTIL_DB')
    AND (
        c.deleted IS NULL
        OR c.deleted > CURRENT_TIMESTAMP - INTERVAL '12 hours'
    )
    AND {database_allowed}
    AND {database_blocked}
    AND CASE {has_fetch_transient} WHEN FALSE THEN NOT t.is_transient::BOOLEAN ELSE TRUE END
