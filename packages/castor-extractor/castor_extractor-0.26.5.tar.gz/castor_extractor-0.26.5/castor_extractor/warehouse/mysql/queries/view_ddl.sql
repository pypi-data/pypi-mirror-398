SELECT
    TABLE_CATALOG AS database_id,
    TABLE_CATALOG AS database_name,
    TABLE_SCHEMA AS schema_id,
    TABLE_SCHEMA AS schema_name,
    TABLE_NAME AS view_name,
    CONCAT('CREATE VIEW ', TABLE_NAME,' AS ', view_definition) AS view_definition
FROM
    INFORMATION_SCHEMA.VIEWS
WHERE TRUE
    AND TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
