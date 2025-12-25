WITH view_count AS(
    SELECT
        canvas_key,
        DATE(loaded_at) AS load_day
    FROM `{project_id}.{dataset_id}.canvas_loads`
    WHERE TRUE
        AND date(loaded_at) = '{extract_date}'
)

SELECT
    canvas_key,
    COUNT(*) AS view_count
FROM view_count
GROUP BY canvas_key
