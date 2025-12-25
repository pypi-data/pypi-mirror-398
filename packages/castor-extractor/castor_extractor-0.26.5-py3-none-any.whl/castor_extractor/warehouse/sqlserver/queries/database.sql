SELECT
    db.database_id,
    database_name = db.name
FROM sys.databases AS db
WHERE db.name NOT IN ('master', 'model', 'msdb', 'tempdb', 'DBAdmin');