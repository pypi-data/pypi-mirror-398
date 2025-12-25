/*
Selects all table lineage events for the given day.
This excludes self-lineage and deduplicates (parent, child) pairs to keep only the most recent lineage event.

Passing parameters is not always supported, so the query must be Python-formatted to set the date.
*/
WITH deduplicated_lineage AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY source_table_full_name, target_table_full_name
               ORDER BY event_time DESC
           ) AS rank
    FROM system.access.table_lineage
    WHERE
        TRUE
        AND event_date = DATE('{day}')
        AND source_table_full_name IS NOT NULL
        AND target_table_full_name IS NOT NULL
        AND source_table_full_name != target_table_full_name
)
SELECT *
FROM deduplicated_lineage
WHERE rank = 1
