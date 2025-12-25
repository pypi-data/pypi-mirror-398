SELECT
    db.oid AS database_id,
    db.datname AS database_name,
    de.description AS "comment"
FROM pg_catalog.pg_database AS db
    LEFT JOIN pg_catalog.pg_description AS de ON de.classoid = db.oid
WHERE db.datname = CURRENT_DATABASE()
