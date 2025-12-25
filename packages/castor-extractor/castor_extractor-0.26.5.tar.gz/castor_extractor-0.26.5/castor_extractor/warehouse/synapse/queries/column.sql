WITH users AS (
    SELECT DISTINCT
        uid,
        name
    FROM sys.sysusers
)

SELECT
    DB_NAME() AS database_id,
    DB_NAME() AS database_name,
    DB_NAME() + '.' + s.name AS schema_id,
    s.name AS schema_name,
    DB_NAME() + '.' + s.name + '.' + o.name AS table_id,
    o.name AS table_name,
    DB_NAME() + '.' + s.name + '.' + o.name + '.' + c.name AS column_id,
    c.name AS column_name,
    COALESCE(su.name, pu.name) AS column_owner,
    COALESCE(su.uid, pu.uid) AS column_owner_id,
    ty.name AS data_type,
    ty.is_nullable AS is_nullable,
    c.max_length AS character_maximum_length,
    o.create_date AS created_at,
    o.modify_date AS updated_at,
    sc.ordinal_position AS ordinal_position,
    NULL AS "comment"
FROM sys.columns AS c
    JOIN sys.objects AS o
        ON c.object_id = o.object_id
    JOIN sys.schemas AS s
        ON s.schema_id = o.schema_id
    JOIN sys.types AS ty
        ON ty.system_type_id = c.system_type_id
    JOIN information_schema.columns AS sc
        ON s.name = sc.table_schema
            AND o.name = sc.table_name
            AND c.name = sc.column_name
    LEFT JOIN users AS pu
        ON s.principal_id = pu.uid
    LEFT JOIN users AS su
        ON o.principal_id = su.uid
WHERE
-- SYNAPSE NOTATION: U for TABLE, V for VIEW
    o.type IN ('U', 'V')
    AND ty.name != 'sysname'
