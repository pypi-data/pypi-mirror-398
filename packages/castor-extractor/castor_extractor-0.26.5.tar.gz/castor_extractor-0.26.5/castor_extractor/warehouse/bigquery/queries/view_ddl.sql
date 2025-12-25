SELECT
    table_catalog AS database_name,
    table_schema AS schema_name,
    table_name AS view_name,
    '{{"project_id": "' || table_catalog || '", "dataset_id": "' || table_schema || '", "table_id": "' || table_name || '"}}' as destination_table,
    view_definition
 FROM `{project}.{dataset}.INFORMATION_SCHEMA.VIEWS`
