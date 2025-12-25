-- This sql file is used to detect SQL sharded tables
-- A table will be classified as sharded if:
--  * The table name is matching a date pattern as suffix (see sharded_name)
--  * There are at least two tables with the same pattern in the same location (dataset.schema)

WITH tables AS (
    SELECT
        table_catalog,
        table_schema,
        table_name,
        creation_time,
        -- we escape brackets for python parameter substitution and colon for sql parameter binding
        REGEXP_REPLACE(table_name, r'(?\:20\d{{6}}T?\d{{0,6}}Z?|1\d{{9}})(?\:__[a-fA-F0-9]{{32}})?$', '*') AS sharded_name
    FROM
        `{project}.region-{region}.INFORMATION_SCHEMA.TABLES`
),

sharded_candidates AS (
    SELECT
        table_catalog,
        table_schema,
        table_name,
        sharded_name,
        COUNT(1) OVER(PARTITION BY table_catalog, table_schema, sharded_name) AS sharded_count,
        -- keep the most recent table (filter on row_number = 1 afterwards)
        ROW_NUMBER() OVER (PARTITION BY table_catalog, table_schema, sharded_name ORDER BY creation_time DESC) AS row_number,
    FROM tables
    WHERE TRUE
      -- when TRUE, the table is a good candidate FOR sharded
      AND table_name != sharded_name
)

SELECT
    table_catalog,
    table_schema,
    table_name,
    sharded_name,
    row_number
FROM
    sharded_candidates
WHERE
     -- remove lonely tables, we don't consider them as sharded
     sharded_count > 1
