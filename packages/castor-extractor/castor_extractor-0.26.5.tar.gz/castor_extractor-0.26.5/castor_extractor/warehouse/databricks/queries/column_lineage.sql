/*
Selects all column lineage events for the given day.
This excludes self-lineage and deduplicates (parent, child) pairs to keep only the most recent lineage event.

Passing parameters is not always supported, so the query must be Python-formatted to set the date.
*/
WITH deduplicated_lineage AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY source_table_full_name, source_column_name, target_table_full_name, target_column_name
               ORDER BY event_time DESC
           ) AS rank
    FROM system.access.column_lineage
    WHERE
        TRUE
        AND event_date = DATE('{day}')
        AND source_table_full_name IS NOT NULL
        AND source_column_name IS NOT NULL
        AND target_table_full_name IS NOT NULL
        AND target_column_name IS NOT NULL
        AND CONCAT(source_table_full_name, '.', source_column_name) != CONCAT(target_table_full_name, '.', target_column_name)
)
SELECT *
FROM deduplicated_lineage
WHERE rank = 1
