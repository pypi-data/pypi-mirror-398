SELECT
    user_name = u.name,
    user_id = u.name
FROM [{database}].sys.database_principals AS u
