WITH parameters AS (
    SELECT
        'pg_%%'::TEXT AS schema_pattern_excluded,
        '{"catalog_history", "information_schema"}'::TEXT[] AS schema_excluded
),

tables AS (
    SELECT
        t.oid AS table_id,
        t.relname AS table_name,
        n.nspname AS schema_name,
        n.oid AS schema_id,
        u.usename AS table_owner,
        t.relowner AS table_owner_id,
        td.description AS "comment",
        t.reltuples::BIGINT AS tuples
    FROM pg_class AS t
        CROSS JOIN parameters AS p
        JOIN pg_catalog.pg_namespace AS n ON n.oid = t.relnamespace
        LEFT JOIN pg_catalog.pg_description AS td ON td.objoid = t.oid AND td.objsubid = 0
        LEFT JOIN pg_catalog.pg_user AS u ON u.usesysid = t.relowner
    WHERE TRUE
        AND n.nspname NOT LIKE p.schema_pattern_excluded
        AND NOT ( n.nspname = ANY(p.schema_excluded) )
        AND t.relam IN (0, 2) -- should not be an index
),

database AS (
    SELECT
        db.datname AS database_name,
        db.oid AS database_id
    FROM pg_catalog.pg_database AS db
    WHERE TRUE
        AND db.datname = CURRENT_DATABASE()
    LIMIT 1
),

meta AS (
    SELECT
        t.table_schema AS schema_name,
        t.table_name AS table_name,
        t.table_type
    FROM information_schema.tables AS t
        CROSS JOIN parameters AS p
    WHERE TRUE
        AND t.table_schema NOT LIKE p.schema_pattern_excluded
        AND NOT ( t.table_schema = ANY(p.schema_excluded) )
),

external_tables AS (
    SELECT
        db.datname AS database_name,
        db.oid::TEXT AS database_id,
        s.schemaname AS schema_name,
        s.esoid::TEXT AS schema_id,
        t.tablename AS table_name,
        db.datname || '.' || s.schemaname || '.' || t.tablename AS table_id,
        u.usename AS table_owner,
        s.esowner AS table_owner_id,
        NULL AS tuples,
        NULL AS "comment",
        'EXTERNAL' AS table_type
    FROM SVV_EXTERNAL_TABLES AS t
        JOIN SVV_EXTERNAL_SCHEMAS AS s ON t.schemaname = s.schemaname
        JOIN pg_catalog.pg_user AS u ON s.esowner = u.usesysid
        JOIN pg_catalog.pg_database AS db ON CURRENT_DATABASE() = db.datname
)

SELECT
    d.database_name,
    d.database_id::TEXT AS database_id,
    t.schema_name,
    t.schema_id::TEXT AS schema_id,
    t.table_name,
    t.table_id::TEXT AS table_id,
    t.table_owner,
    t.table_owner_id,
    t.tuples,
    t.comment,
    COALESCE(m.table_type, 'BASE TABLE') AS table_type
FROM tables AS t
    CROSS JOIN database AS d
    LEFT JOIN meta AS m ON (t.table_name = m.table_name AND t.schema_name = m.schema_name)

UNION DISTINCT

SELECT * FROM external_tables
