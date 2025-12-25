SELECT
    db.oid AS database_id,
    db.datname AS database_name,
    dd.description AS "comment"
FROM pg_catalog.pg_database AS db
    LEFT JOIN pg_catalog.pg_description AS dd ON dd.classoid = db.oid
-- when cross database query goes public this will evolve
WHERE db.datname = CURRENT_DATABASE()
