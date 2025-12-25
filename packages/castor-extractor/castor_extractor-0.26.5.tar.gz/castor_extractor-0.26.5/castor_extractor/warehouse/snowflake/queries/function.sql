SELECT
    f.function_name AS name,
    CONCAT(f.function_catalog, '.', f.function_schema, '.', f.function_name) AS path,
    f.argument_signature AS signature,
    f.function_definition AS definition
FROM snowflake.account_usage.functions f
WHERE TRUE
    AND f.function_catalog NOT IN ('SNOWFLAKE', 'UTIL_DB')
    AND f.function_language = 'SQL'
    AND deleted IS NULL
