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
        table_owner_id = principal_id,
        schema_id
    FROM
        [{database}].sys.tables

    UNION

    SELECT
        table_id = object_id,
        table_name = name,
        table_owner_id = principal_id,
        schema_id
    FROM
        [{database}].sys.views

    UNION

    SELECT
        table_id = object_id,
        table_name = name,
        table_owner_id = principal_id,
        schema_id
    FROM
        [{database}].sys.external_tables
),
/*
`sys.columns` contains, among others:
- an object_id, which is the table ID
- a column_ID

`extended_properties`:
- to get information about a column, join on (major_id, minor_id) = (table ID, column ID)
- to get information about a table, join on (major_id, minor_id) = (table ID, 0)
*/
-- Create the column identifiers
column_ids AS (
    SELECT
        sd.database_id,
        database_name = sd.name,
        column_id = sc.column_id,
        column_name = sc.name,
        table_id,
        table_name,
        schema_name = ss.name,
        schema_id = ss.schema_id,
        comment = CONVERT(varchar(1024), ep.value)
    FROM [{database}].sys.columns AS sc
    LEFT JOIN extended_tables AS et ON sc.object_id = et.table_id
    LEFT JOIN [{database}].sys.schemas AS ss ON et.schema_id = ss.schema_id
    LEFT JOIN [{database}].sys.databases AS sd ON sd.name = '{database}'
    LEFT JOIN [{database}].sys.extended_properties AS ep
        ON
            sc.object_id = ep.major_id
            AND sc.column_id = ep.minor_id
            AND ep.name = 'MS_Description'
),

columns AS (
    SELECT
        i.database_name,
        i.database_id,
        schema_name = c.table_schema,
        schema_id = CAST(i.database_id AS VARCHAR(10)) + '_' + CAST(i.schema_id AS VARCHAR(10)),
        table_name = c.table_name,
        table_id = CAST(i.database_id AS VARCHAR(10)) + '_' + CAST(i.schema_id AS VARCHAR(10)) + '_' + CAST(i.table_id AS VARCHAR(10)),
        c.column_name,
        c.data_type,
        c.ordinal_position,
        c.column_default,
        c.is_nullable,
        c.character_maximum_length,
        c.character_octet_length,
        c.numeric_precision,
        c.numeric_precision_radix,
        c.numeric_scale,
        c.datetime_precision,
        i.comment,
        column_id = CONCAT(i.table_id, '.', c.column_name)
    FROM
        [{database}].INFORMATION_SCHEMA.COLUMNS AS c
    LEFT JOIN column_ids AS i
        ON
            (
                c.table_name COLLATE DATABASE_DEFAULT = i.table_name COLLATE DATABASE_DEFAULT
                AND c.table_schema COLLATE DATABASE_DEFAULT = i.schema_name COLLATE DATABASE_DEFAULT
                AND c.column_name COLLATE DATABASE_DEFAULT = i.column_name COLLATE DATABASE_DEFAULT
            )
)

SELECT * FROM columns
