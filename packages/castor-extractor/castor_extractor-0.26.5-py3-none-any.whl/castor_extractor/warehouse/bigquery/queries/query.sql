SELECT
    job_id AS query_id,
    creation_time,
    project_id AS database_name,
    user_email AS user_name,
    user_email AS user_id,
    job_type,
    statement_type,
    priority,
    start_time,
    end_time,
    query AS query_text,
    state,
    reservation_id,
    total_bytes_processed,
    total_bytes_billed,
    total_slot_ms,
    error_result,
    cache_hit,
    destination_table,
    referenced_tables,
    labels,
    parent_job_id
FROM `{project}.region-{region}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE TRUE
    AND DATE(creation_time) = :day
    AND EXTRACT(hour FROM creation_time) BETWEEN :hour_min AND :hour_max
    AND job_type = 'QUERY'
