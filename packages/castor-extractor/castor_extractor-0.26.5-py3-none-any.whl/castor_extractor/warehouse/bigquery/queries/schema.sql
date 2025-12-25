SELECT
    catalog_name AS database_id,
    catalog_name AS database_name,
    schema_name,
    schema_owner,
    creation_time,
    last_modified_time,
    location,
    CONCAT(catalog_name, '.', schema_name) AS schema_id
FROM `{project}.region-{region}.INFORMATION_SCHEMA.SCHEMATA`
