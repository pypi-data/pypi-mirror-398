/*
Select all types of tables:
- Views
- Base Tables
- External Tables
*/
WITH extended_tables AS (
    SELECT
        table_id = object_id,
        table_name = name,
        principal_id,
        schema_id
    FROM
        [{database}].sys.tables

    UNION

    SELECT
        table_id = object_id,
        table_name = name,
        principal_id,
        schema_id
    FROM
        [{database}].sys.views

    UNION

    SELECT
        table_id = object_id,
        table_name = name,
        principal_id,
        schema_id
    FROM
        [{database}].sys.external_tables
),
-- Get the row count per table
partitions AS (
    SELECT
        object_id,
        row_count = SUM(rows)
    FROM [{database}].sys.partitions
    GROUP BY object_id
),
-- Append row count to table properties
extended_tables_with_row_count AS (
    SELECT
        et.*,
        row_count
    FROM
        extended_tables AS et
    LEFT JOIN partitions AS p
        ON et.table_id = p.object_id

),

/*
`extended_properties`:
- to get information about a column, join on (major_id, minor_id) = (table ID, column ID)
- to get information about a table, join on (major_id, minor_id) = (table ID, 0)
*/
-- Generate table identifiers and fetch table description
table_ids AS (
    SELECT
        table_id,
        table_name,
        schema_name = ss.name,
        schema_id = ss.schema_id,
        table_owner_id = u.name,
        table_owner = u.name,
        row_count,
        comment = CONVERT(varchar(1024), ep.value)
    FROM extended_tables_with_row_count AS et
    LEFT JOIN [{database}].sys.schemas AS ss
        ON et.schema_id = ss.schema_id
    LEFT JOIN [{database}].sys.database_principals AS u
        ON et.principal_id = u.principal_id
    LEFT JOIN [{database}].sys.extended_properties AS ep
        ON (
            et.table_id = ep.major_id
            AND ep.minor_id = 0
            AND ep.name = 'MS_Description'
        )
),

meta AS (
    SELECT
        database_name = t.table_catalog,
        database_id = db.database_id,
        schema_name = t.table_schema,
        t.table_name,
        t.table_type
    FROM
        [{database}].INFORMATION_SCHEMA.TABLES AS t
    LEFT JOIN [{database}].sys.databases AS db
        ON t.table_catalog COLLATE DATABASE_DEFAULT = db.name COLLATE DATABASE_DEFAULT
)

SELECT
    m.database_name,
    m.database_id,
    m.schema_name,
    schema_id = CAST(m.database_id AS VARCHAR(10)) + '_' + CAST(i.schema_id AS VARCHAR(10)),
    m.table_name,
    table_id = CAST(m.database_id AS VARCHAR(10)) + '_' + CAST(i.schema_id AS VARCHAR(10)) + '_' + CAST(i.table_id AS VARCHAR(10)),
    m.table_type,
    i.table_owner,
    i.table_owner_id,
    i.comment,
    tuples = i.row_count
FROM
    meta AS m
LEFT JOIN table_ids AS i
    ON (m.table_name = i.table_name AND m.schema_name = i.schema_name)
