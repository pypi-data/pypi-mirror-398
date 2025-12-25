WITH d AS (
    SELECT
        table_catalog,
        table_schema,
        table_name,
        option_value AS `comment`
    FROM
        -- we use double brackets because we format this file in two steps, first sharded_statement is filled, then project and region.
        `{{project}}.region-{{region}}.INFORMATION_SCHEMA.TABLE_OPTIONS`
    WHERE TRUE
        AND option_name = 'description'
        AND option_value IS NOT NULL
        AND option_value != ''
        AND option_value != '""'
),

sharded AS ({sharded_statement})

SELECT
    i.table_catalog AS database_name,
    i.table_catalog AS database_id,
    i.table_schema AS `schema_name`,
    COALESCE(s.sharded_name, i.table_name) AS table_name,
    i.table_type,
    i.is_insertable_into,
    i.is_typed,
    i.creation_time,
    d.comment,
    NULL AS tags, -- only fetched when settings are activated
    CONCAT(i.table_catalog, '.', i.table_schema) AS schema_id,
    CONCAT(i.table_catalog, '.', i.table_schema, '.', COALESCE(s.sharded_name, i.table_name)) AS table_id
FROM
    `{{project}}.region-{{region}}.INFORMATION_SCHEMA.TABLES` AS i
LEFT JOIN d ON i.table_catalog = d.table_catalog
                   AND i.table_schema = d.table_schema
                   AND i.table_name = d.table_name
LEFT JOIN sharded s ON i.table_catalog = s.table_catalog
                AND i.table_schema = s.table_schema
                AND i.table_name = s.table_name
WHERE TRUE
    AND (s.table_name IS NULL OR s.row_number = 1) -- keep only one sharded
