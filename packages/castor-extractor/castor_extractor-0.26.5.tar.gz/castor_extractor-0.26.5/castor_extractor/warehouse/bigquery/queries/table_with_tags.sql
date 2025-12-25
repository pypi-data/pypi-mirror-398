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
t AS
(
    SELECT
        table_catalog,
        table_schema,
        table_name,
        option_value AS tags
    FROM
        `{{project}}.region-{{region}}.INFORMATION_SCHEMA.TABLE_OPTIONS`
    WHERE TRUE
        AND option_name = 'labels'
        AND option_value IS NOT NULL
        AND option_value != ''
        AND option_value != '""'
),

-- reading table `INFORMATION_SCHEMA.SCHEMATA_OPTIONS` require specific permissions that are not included in the onboarding process yet
-- that's why we only fetch tags when settings are activated
dt AS
(
    SELECT
        catalog_name,
        schema_name,
        option_value AS tags
    FROM
        `{{project}}.region-{{region}}.INFORMATION_SCHEMA.SCHEMATA_OPTIONS`
    WHERE TRUE
        AND option_name = 'labels'
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
    CONCAT(
        COALESCE(t.tags, ""),
        COALESCE(dt.tags, "")
    ) AS tags,
    CONCAT(i.table_catalog, '.', i.table_schema) AS schema_id,
    CONCAT(i.table_catalog, '.', i.table_schema, '.', COALESCE(s.sharded_name, i.table_name)) AS table_id
FROM
    `{{project}}.region-{{region}}.INFORMATION_SCHEMA.TABLES` AS i
LEFT JOIN d ON i.table_catalog = d.table_catalog
                   AND i.table_schema = d.table_schema
                   AND i.table_name = d.table_name
LEFT JOIN t ON i.table_catalog = t.table_catalog
                AND i.table_schema = t.table_schema
                AND i.table_name = t.table_name
LEFT JOIN dt ON i.table_catalog = dt.catalog_name
                AND i.table_schema = dt.schema_name
LEFT JOIN sharded s ON i.table_catalog = s.table_catalog
                AND i.table_schema = s.table_schema
                AND i.table_name = s.table_name
WHERE TRUE
    AND (s.table_name IS NULL OR s.row_number = 1) -- keep only one sharded
