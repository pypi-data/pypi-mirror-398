/*
Gets the query jobs triggered by Looker Studio when refreshing a BigQuery data source. Only the latest query per
data source is selected.

The `labels` column should indicate the `looker_studio_datasource_id` that triggered the job. In some cases, it also
contains a `looker_studio_report_id` value, which gives us a link between the data source and a report.
*/
WITH ranked_by_datasource AS (
    SELECT
        creation_time,
        project_id AS database_name,
        user_email,
        query AS query_text,
        referenced_tables,
        labels,
        ROW_NUMBER() OVER (
            PARTITION BY (
                SELECT
                    label.value
                FROM
                    UNNEST(labels) AS label
                WHERE
                    label.key = 'looker_studio_datasource_id'
            )
            ORDER BY
                creation_time DESC
        ) AS row_num
    FROM
        `{project}.region-{region}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
    WHERE
        job_type = 'QUERY'
        AND ARRAY_LENGTH(referenced_tables) > 0
        AND EXISTS (
            SELECT
                1
            FROM
                UNNEST(labels) AS label
            WHERE
                label.key = 'requestor'
                AND label.value = 'looker_studio'
        )
)
SELECT
    creation_time,
    database_name,
    user_email,
    query_text,
    referenced_tables,
    labels
FROM
    ranked_by_datasource
WHERE
    row_num = 1;
