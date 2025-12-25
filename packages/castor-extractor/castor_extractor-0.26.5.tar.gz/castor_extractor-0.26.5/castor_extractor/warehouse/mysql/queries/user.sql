SELECT
    CONCAT(User, '@', Host) AS user_id,
    User AS user_name,
    Super_priv AS super_priv,
    User_attributes->>"$.comment" AS comment
FROM mysql.user
