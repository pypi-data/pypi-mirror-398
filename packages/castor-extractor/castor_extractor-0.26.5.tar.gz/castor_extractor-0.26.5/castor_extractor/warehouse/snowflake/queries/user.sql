SELECT
    name,
    created_on,
    deleted_on,
    login_name,
    display_name,
    first_name,
    last_name,
    email,
    has_password,
    disabled,
    snowflake_lock,
    default_warehouse,
    default_namespace,
    default_role,
    bypass_mfa_until,
    last_success_login,
    -- prevent dates exceeding python parsing
    IFF(
        expires_at IS NULL
        OR EXTRACT(YEAR FROM expires_at) > 2100,
        NULL,
        expires_at
    ) AS expires_at,
    locked_until_time,
    password_last_set_time,
    comment
FROM snowflake.account_usage.users
