SELECT
    db.oid AS database_id,
    db.datname AS database_name,
    n.oid::TEXT AS schema_id,
    n.nspname AS schema_name,
    u.usename AS schema_owner,
    u.usesysid AS schema_owner_id,
    sd.description AS "comment"
FROM pg_catalog.pg_namespace AS n
    CROSS JOIN pg_catalog.pg_database AS db
    JOIN pg_catalog.pg_user AS u ON u.usesysid = n.nspowner
    LEFT JOIN pg_catalog.pg_description AS sd ON sd.classoid = n.oid
WHERE TRUE
    AND db.datname = CURRENT_DATABASE()
    AND n.nspname NOT LIKE 'pg_%%'
    AND n.nspname NOT IN ('catalog_history', 'information_schema')
