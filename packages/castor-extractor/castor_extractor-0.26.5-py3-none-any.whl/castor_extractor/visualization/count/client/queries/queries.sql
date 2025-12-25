WITH ranked_queries AS (
    SELECT
        cell_key,
        connection_key,
        query,
        started_at,
        ROW_NUMBER() OVER (
            PARTITION BY cell_key
            ORDER BY started_at DESC
        ) AS rank
    FROM `{project_id}.{dataset_id}.queries`
    WHERE TRUE
        AND DATE(started_at) = '{extract_date}'
)

SELECT
    cell_key,
    connection_key,
    query,
    started_at
FROM ranked_queries
WHERE TRUE
    AND rank = 1
