WITH ids AS (
    SELECT
        db.datname AS database_name,
        db.oid AS database_id,
        t.oid AS table_id,
        t.relname AS table_name,
        n.nspname AS schema_name,
        n.oid AS schema_id
    FROM pg_class AS t
        JOIN pg_catalog.pg_namespace AS n ON n.oid = t.relnamespace
        CROSS JOIN pg_catalog.pg_database AS db
    WHERE TRUE
        AND db.datname = CURRENT_DATABASE()
        AND n.nspname NOT LIKE 'pg_%%'
        AND n.nspname NOT IN ('catalog_history', 'information_schema')
        AND t.relam IN (0, 2) -- should not be an index
),

information_tables AS (
    SELECT
        i.database_name,
        i.database_id,
        c.table_schema AS schema_name,
        i.schema_id,
        c.table_name AS table_name,
        i.table_id,
        c.column_name,
        i.table_id || '.' || c.column_name AS column_id,
        c.data_type,
        c.ordinal_position,
        c.is_nullable,
        c.character_maximum_length,
        c.character_octet_length,
        c.numeric_precision,
        c.numeric_precision_radix,
        c.numeric_scale,
        c.datetime_precision,
        c.interval_precision,
        c.interval_type,
        d.description AS "comment"
    FROM information_schema.columns AS c
        JOIN ids AS i
            ON c.table_schema = i.schema_name AND c.table_name = i.table_name
        LEFT JOIN pg_catalog.pg_description AS d
            ON d.objoid = i.table_id AND d.objsubid = c.ordinal_position
),

raw_tables AS (
    -- some table might be missing from information_schema.columns
    -- this is a fallback fetching from lower level pg tables
    SELECT
        i.database_name,
        i.database_id,
        n.nspname AS schema_name,
        n.oid AS schema_id,
        c.relname AS table_name,
        c.oid AS table_id,
        a.attname AS column_name,
        c.oid::TEXT || '.' || a.attname AS column_id,
        a.attnum AS ordinal_position,
        CASE
            WHEN t.typname = 'bpchar' THEN 'char'
            ELSE t.typname
        END AS data_type,
        CASE a.attnotnull WHEN TRUE THEN 'NO' ELSE 'YES' END AS is_nullable
    FROM pg_attribute AS a
        JOIN pg_type AS t ON t.oid = a.atttypid -- type
        JOIN pg_class AS c ON c.oid = a.attrelid -- table
        LEFT JOIN pg_attrdef AS ad ON ( ad.adrelid = c.oid AND ad.adnum = a.attnum ) -- default
        JOIN pg_namespace AS n ON n.oid = c.relnamespace -- schema
        JOIN ids AS i ON n.nspname = i.schema_name AND c.relname = i.table_name -- database
    WHERE TRUE
        AND c.relname NOT LIKE '%%pkey'
        AND a.attnum >= 0
        AND t.typname NOT IN ('xid', 'cid', 'oid', 'tid', 'name')
),

tables AS (
    SELECT
        COALESCE(i.database_name, r.database_name) AS database_name,
        COALESCE(i.database_id, r.database_id)::TEXT AS database_id,
        COALESCE(i.schema_name, r.schema_name) AS schema_name,
        COALESCE(i.schema_id, r.schema_id)::TEXT AS schema_id,
        COALESCE(i.table_name, r.table_name) AS table_name,
        COALESCE(i.table_id, r.table_id)::TEXT AS table_id,
        COALESCE(i.column_name, r.column_name) AS column_name,
        COALESCE(i.column_id, r.column_id) AS column_id,
        COALESCE(i.data_type, r.data_type) AS data_type,
        COALESCE(i.ordinal_position, r.ordinal_position) AS ordinal_position,
        COALESCE(i.is_nullable, r.is_nullable) AS is_nullable,
        i.character_maximum_length::INT AS character_maximum_length,
        i.character_octet_length::INT AS character_octet_length,
        i.numeric_precision::INT AS numeric_precision,
        i.numeric_precision_radix::INT AS numeric_precision_radix,
        i.numeric_scale::INT AS numeric_scale,
        i.datetime_precision::INT AS datetime_precision,
        i.interval_precision::TEXT AS interval_precision,
        i.interval_type::TEXT AS interval_type,
        i.comment::TEXT AS "comment"
    FROM raw_tables AS r
        LEFT JOIN information_tables AS i ON (i.table_id = r.table_id AND i.column_name = r.column_name)
),

views_late_binding AS (
    SELECT
        i.database_name,
        i.database_id::TEXT AS database_id,
        c.schema_name,
        i.schema_id::TEXT AS schema_id,
        c.table_name,
        i.table_id::TEXT AS table_id,
        c.column_name,
        i.table_id::TEXT || '.' || c.column_name AS column_id,
        c.data_type,
        c.ordinal_position,
        'YES' AS is_nullable,
        NULL::INT AS character_maximum_length,
        NULL::INT AS character_octet_length,
        NULL::INT AS numeric_precision,
        NULL::INT AS numeric_precision_radix,
        NULL::INT AS numeric_scale,
        NULL::INT AS datetime_precision,
        NULL::TEXT AS interval_precision,
        NULL::TEXT AS interval_type,
        NULL::TEXT AS "comment"
    FROM (
        SELECT
            schema_name,
            table_name,
            column_name,
            MIN(data_type) AS data_type,
            MIN(ordinal_position) AS ordinal_position
        FROM PG_GET_LATE_BINDING_VIEW_COLS()
        -- syntax specific to this redshift system table
        COLS(
            schema_name NAME,
            table_name NAME,
            column_name NAME,
            data_type VARCHAR,
            ordinal_position INT
        )
        GROUP BY 1, 2, 3
    ) AS c
    JOIN ids AS i
        ON c.schema_name = i.schema_name AND c.table_name = i.table_name
),

external_columns AS (
    SELECT
        db.datname AS database_name,
        db.oid::TEXT AS database_id,
        s.schemaname AS schema_name,
        s.esoid::TEXT AS schema_id,
        c.tablename AS table_name,
        db.datname || '.' || s.schemaname || '.' || c.tablename AS table_id,
        c.columnname AS column_name,
        db.datname || '.' || s.schemaname || '.' || c.tablename || '.' || c.columnname AS column_id,
        MIN(c.external_type) AS data_type,
        MIN(c.columnnum) AS ordinal_position,
        MIN(CASE c.is_nullable WHEN 'false' THEN 'NO' ELSE 'YES' END) AS is_nullable,
        NULL AS character_maximum_length,
        NULL AS character_octet_length,
        NULL AS numeric_precision,
        NULL AS numeric_precision_radix,
        NULL AS numeric_scale,
        NULL AS datetime_precision,
        NULL AS interval_precision,
        NULL AS interval_type,
        NULL AS "comment"
    FROM SVV_EXTERNAL_COLUMNS AS c
        JOIN SVV_EXTERNAL_SCHEMAS AS s ON c.schemaname = s.schemaname
        JOIN pg_catalog.pg_database AS db ON CURRENT_DATABASE() = db.datname

    -- To remove duplicate column names that can occur in external tables (no check on CSVs)
    GROUP BY database_name, database_id, schema_name, schema_id, table_name, table_id, column_name, column_id
)

SELECT * FROM tables

UNION DISTINCT

SELECT * FROM views_late_binding

UNION DISTINCT

SELECT * FROM external_columns
