WITH view_owner AS (
    SELECT
        TABLE_NAME AS table_name,
        DEFINER AS owner
    FROM
        INFORMATION_SCHEMA.VIEWS
)

SELECT
    TABLE_CATALOG AS database_id,
    TABLE_CATALOG AS database_name,
    TABLE_SCHEMA AS schema_id,
    TABLE_SCHEMA AS schema_name,
    CONCAT(TABLE_SCHEMA, '.', t.TABLE_NAME) AS table_id,
    t.TABLE_NAME AS table_name,
    TABLE_TYPE AS table_type, -- either BASE TABLE or VIEW
    TABLE_ROWS AS tuples,
    AVG_ROW_LENGTH AS row_bytes,
    CREATE_TIME AS created_at,
    UPDATE_TIME AS updated_at,
    owner AS table_owner,
    CASE
        WHEN TABLE_TYPE = 'VIEW' OR TABLE_COMMENT = '' THEN NULL
        ELSE TABLE_COMMENT
    END AS comment
FROM
    INFORMATION_SCHEMA.TABLES AS t
    LEFT JOIN view_owner ON t.TABLE_NAME = view_owner.table_name
WHERE TRUE
    AND TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
