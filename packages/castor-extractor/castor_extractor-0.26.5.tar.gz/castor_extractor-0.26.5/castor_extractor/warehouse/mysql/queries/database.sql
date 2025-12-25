/*
 In MySQL, "database" and "schema" are aliases and hence represent the same thing.
 However, in the metadata table there is also the mention of a catalog, which is always set to "def".
 We will use this catalog ad the database.
 */
WITH unique_catalog AS (
    SELECT DISTINCT TABLE_CATALOG AS database_name
    FROM INFORMATION_SCHEMA.TABLES
)

SELECT
    database_name AS database_id,
    database_name
FROM unique_catalog
