WITH creations AS (
    SELECT
        pci.reloid AS table_id,
        pci.relcreationtime AS created_at
    FROM pg_class_info AS pci
    WHERE TRUE
        AND pci.relcreationtime IS NOT NULL -- holding a creation time
        AND pci.reltype != 0 -- tables only
),

inserts AS (
    SELECT
        tbl AS table_id,
        MAX(endtime) AS updated_at
    FROM stl_insert
    GROUP BY 1
)

SELECT
    n.nspname AS schema_name,
    t.relname AS table_name,
    c.table_id,
    c.created_at,
    i.updated_at
FROM creations AS c
    LEFT JOIN inserts AS i ON i.table_id = c.table_id
    LEFT JOIN pg_catalog.pg_class AS t ON t.oid = c.table_id
    LEFT JOIN pg_catalog.pg_namespace AS n ON n.oid = t.relnamespace
ORDER BY 1, 2
