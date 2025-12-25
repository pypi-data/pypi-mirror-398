SELECT
    TABLE_CATALOG AS database_id,
    TABLE_CATALOG AS database_name,
    TABLE_SCHEMA AS schema_id,
    TABLE_SCHEMA AS schema_name,
    CONCAT(TABLE_SCHEMA, '.', TABLE_NAME) AS table_id,
    TABLE_NAME AS table_name,
    CONCAT(TABLE_SCHEMA, '.', TABLE_NAME, '.', COLUMN_NAME) AS column_id,
    COLUMN_NAME AS column_name,
    ORDINAL_POSITION AS ordinal_position,
    COLUMN_DEFAULT AS column_default,
    IS_NULLABLE AS is_nullable,
    DATA_TYPE AS data_type,
    CHARACTER_MAXIMUM_LENGTH AS character_maximum_length,
    NUMERIC_PRECISION AS numeric_precision,
    NUMERIC_SCALE AS numeric_scale,
    DATETIME_PRECISION AS datetime_precision,
    COLUMN_TYPE AS column_type,
    COLUMN_KEY AS column_key,
    COLUMN_COMMENT AS comment
FROM
    INFORMATION_SCHEMA.COLUMNS
WHERE TRUE
    AND TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
