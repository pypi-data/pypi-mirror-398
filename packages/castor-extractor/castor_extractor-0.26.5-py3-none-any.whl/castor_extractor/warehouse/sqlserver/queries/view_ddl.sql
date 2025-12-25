SELECT
    v.name AS view_name,
    m.definition AS view_definition,
    s.name AS schema_name,
    DB_NAME() AS database_name
FROM
    [{database}].sys.views v
INNER JOIN
    [{database}].sys.schemas s
    ON v.schema_id = s.schema_id
INNER JOIN
    [{database}].sys.sql_modules m
    ON v.object_id = m.object_id
