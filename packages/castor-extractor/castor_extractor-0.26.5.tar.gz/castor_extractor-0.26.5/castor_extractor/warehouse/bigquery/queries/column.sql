WITH field_path AS (
    SELECT
        table_catalog,
        table_schema,
        table_name,
        column_name,
        description,
        field_path,
        data_type
    FROM
        -- we use double brackets because we format this file in two steps, first sharded_statement is filled, then project and region.
        `{{project}}.region-{{region}}.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
),

sharded AS ({sharded_statement})

SELECT
    c.table_catalog AS database_id,
    c.table_catalog AS database_name,
    c.table_schema AS `schema_name`,
    COALESCE(s.sharded_name, c.table_name) AS table_name,
    f.field_path AS column_name,
    c.ordinal_position,
    c.is_nullable,
    f.data_type,
    c.is_generated,
    c.generation_expression,
    c.is_stored,
    c.is_hidden,
    c.is_updatable,
    c.is_system_defined,
    c.is_partitioning_column,
    c.clustering_ordinal_position,
    f.description AS `comment`,
    CONCAT(c.table_catalog, '.', c.table_schema) AS schema_id,
    CONCAT(c.table_catalog, '.', c.table_schema, '.', COALESCE(s.sharded_name, c.table_name)) AS table_id,
    CONCAT(c.table_catalog, '.', c.table_schema, '.', COALESCE(s.sharded_name, c.table_name), '.', f.field_path) AS column_id
FROM
    `{{project}}.region-{{region}}.INFORMATION_SCHEMA.COLUMNS` AS c
    LEFT JOIN field_path AS f ON
            c.table_catalog = f.table_catalog
            AND c.table_schema = f.table_schema
            AND c.table_name = f.table_name
            AND c.column_name = f.column_name
    LEFT JOIN sharded AS s ON
            c.table_catalog = s.table_catalog
            AND c.table_schema = s.table_schema
            AND c.table_name = s.table_name
WHERE TRUE
    AND c.column_name != '_PARTITIONTIME'
    AND (s.table_name IS NULL OR s.row_number = 1) -- keep only one sharded
