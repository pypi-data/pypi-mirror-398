SELECT
    usename AS user_name,
    usesysid AS user_id,
    usecreatedb AS has_create_db,
    usesuper AS is_super,
    valuntil AS valid_until
FROM pg_catalog.pg_user
