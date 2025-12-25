WITH catalogs AS (
    SELECT DISTINCT catalog_name
    FROM `{project}.region-{region}.INFORMATION_SCHEMA.SCHEMATA`
)
SELECT
    catalog_name AS database_id,
    catalog_name AS database_name
FROM catalogs
