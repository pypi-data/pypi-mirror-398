WITH ids AS (
    SELECT
        d.datname AS database_name,
        d.oid AS database_id,
        t.oid AS table_id,
        t.relname AS table_name,
        n.nspname AS schema_name,
        n.oid AS schema_id
    FROM
        pg_class AS t
        JOIN pg_catalog.pg_namespace AS n ON n.oid = t.relnamespace
        CROSS JOIN pg_catalog.pg_database AS d
    WHERE
        TRUE
        AND d.datname = CURRENT_DATABASE()
        AND n.nspname NOT LIKE 'pg_%%'
        AND n.nspname NOT IN ('catalog_history', 'information_schema')
        AND t.relam IN (0, 2) -- should not be an index
),

columns AS (
    SELECT
        ids.database_name,
        ids.database_id,
        c.table_schema AS schema_name,
        ids.schema_id,
        c.table_name AS table_name,
        ids.table_id,
        c.column_name,
        ids.table_id || '.' || c.column_name AS column_id,
        c.data_type,
        c.ordinal_position,
        c.column_default,
        c.is_nullable,
        c.character_maximum_length,
        c.character_octet_length,
        c.numeric_precision,
        c.numeric_precision_radix,
        c.numeric_scale,
        c.datetime_precision,
        c.interval_precision,
        c.interval_type,
        c.interval_precision,
        d.description AS "comment"
    FROM
        information_schema.columns AS c
        JOIN ids ON c.table_schema = ids.schema_name
                    AND c.table_name = ids.table_name
        LEFT JOIN pg_catalog.pg_description AS d ON d.objoid = ids.table_id
                                                    AND d.objsubid = c.ordinal_position
)

SELECT
    *
FROM
    columns
