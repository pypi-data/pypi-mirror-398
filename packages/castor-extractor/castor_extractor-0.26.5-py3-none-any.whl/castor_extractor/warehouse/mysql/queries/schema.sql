/*
 Extract information about schemas (schemas and databases are the same in MySQL).
 Schemas don't have a creation time, so we pick the creation time of the first table created within the schema.
 */
WITH creation_times AS (
    SELECT
        TABLE_SCHEMA AS schema_name,
        MIN(CREATE_TIME) AS creation_time
    FROM INFORMATION_SCHEMA.TABLES
    GROUP BY schema_name
)

SELECT
    sch.CATALOG_NAME AS database_id,
    sch.CATALOG_NAME AS database_name,
    sch.SCHEMA_NAME AS schema_id,
    sch.SCHEMA_NAME AS schema_name,
    ct.creation_time
FROM INFORMATION_SCHEMA.SCHEMATA AS sch
LEFT JOIN creation_times AS ct ON sch.SCHEMA_NAME = ct.SCHEMA_NAME
WHERE TRUE
    AND sch.SCHEMA_NAME NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
