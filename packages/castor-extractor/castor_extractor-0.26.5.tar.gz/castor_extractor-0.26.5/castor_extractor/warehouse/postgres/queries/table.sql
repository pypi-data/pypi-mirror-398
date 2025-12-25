WITH ids AS (
    SELECT
        t.oid AS table_id,
        t.relname AS table_name,
        n.nspname AS schema_name,
        n.oid AS schema_id,
        r.rolname AS table_owner,
        t.relowner AS table_owner_id,
        td.description AS "comment",
        t.reltuples::BIGINT AS tuples
    FROM pg_class AS t
        JOIN pg_catalog.pg_namespace AS n ON n.oid = t.relnamespace
        LEFT JOIN pg_catalog.pg_description AS td ON td.objoid = t.oid AND td.objsubid = 0
        LEFT JOIN pg_catalog.pg_roles AS r ON r.oid = t.relowner
    WHERE TRUE
        AND n.nspname NOT LIKE 'pg_%%'
        AND n.nspname NOT IN ('catalog_history', 'information_schema')
        AND t.relam IN (0, 2) -- should not be an index
),

meta AS (
    SELECT
        db.datname AS database_name,
        db.oid AS database_id,
        t.table_schema AS schema_name,
        t.table_name AS table_name,
        t.table_type
    FROM information_schema.tables AS t
        CROSS JOIN pg_catalog.pg_database AS db
    WHERE TRUE
        AND db.datname = CURRENT_DATABASE()
        AND t.table_schema NOT LIKE 'pg_%%'
        AND t.table_schema NOT IN ('catalog_history', 'information_schema')
)

SELECT
    m.database_name,
    m.database_id,
    m.schema_name,
    i.schema_id,
    m.table_name,
    i.table_id,
    m.table_type,
    i.table_owner,
    i.table_owner_id,
    i.tuples,
    i.comment
FROM meta AS m
    JOIN ids AS i ON (i.table_name = m.table_name AND i.schema_name = m.schema_name)
