/*
This query was inspired from this thread:
https://github.com/awslabs/amazon-redshift-utils/blob/master/src/AdminViews/v_generate_view_ddl.sql

Notable differences:
* There is no "--DROP" statement/comment here
* Left-trimming the view definition is necessary to capture "CREATE" statements starting with whitespaces or line breaks.
 */

SELECT
    CURRENT_DATABASE() AS database_name,
    n.nspname AS schema_name,
    c.relname AS view_name,
    CASE
        WHEN c.relnatts > 0 THEN
            CASE
                STRPOS(LOWER(LTRIM(pg_get_viewdef(c.oid, TRUE), '\t\r\n ')), 'create')
                WHEN 1 THEN '' -- CREATE statement already present
                ELSE           -- No CREATE statement present, so no materialized view anyway
                    'CREATE OR REPLACE VIEW ' || QUOTE_IDENT(n.nspname) || '.' || QUOTE_IDENT(c.relname) || ' AS\n'
            END
            || COALESCE(pg_get_viewdef(c.oid, TRUE), '')
        ELSE COALESCE(pg_get_viewdef(c.oid, TRUE), '')
    END AS view_definition
FROM
    pg_catalog.pg_class AS c
INNER JOIN
    pg_catalog.pg_namespace AS n
    ON c.relnamespace = n.oid
WHERE
    TRUE
    AND relkind = 'v'
    AND n.nspname NOT IN ('information_schema', 'pg_catalog');
