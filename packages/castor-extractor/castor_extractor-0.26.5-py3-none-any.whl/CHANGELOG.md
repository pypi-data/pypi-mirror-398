# Changelog

## 0.26.5 - 2025-12-23

* Looker: extract dashboard's slug

## 0.26.4 - 2025-12-18

* Snowflake: extend query_blocked to column-lineage extraction

## 0.26.3 - 2025-12-17

* Tableau: catch error relationship-service-war

## 0.26.2 - 2025-12-16

* Notion: deduplicate Users

## 0.26.1 - 2025-12-15

* Power BI: pages extraction conditioned on workspace access

## 0.26.0 - 2025-12-09

* Removing support for python3.9

## 0.25.29 - 2025-12-11

* Tableau: dynamic pagination and safe mode for all types of assets

## 0.25.28 - 2025-12-08

* Tableau: fix retry exponential time

## 0.25.27 - 2025-12-04

* Sigma: retry on 503 errors

## 0.25.26 - 2025-12-03

* Strategy: deduplicate users on ID

## 0.25.25 - 2025-12-02

* Tableau: better catching of timeouts

## 0.25.24 - 2025-11-27

* Tableau: extraction of tables and columns without "Extracts"

## 0.25.23 - 2025-11-24

* Looker Studio: add option to extract source queries only

## 0.25.22 - 2025-11-19

* SQL Server: improved error log
* Sigma : handle service errors in queries and elements extraction

## 0.25.21 - 2025-11-05

* Qlik: Extracting sheets

## 0.25.20 - 2025-11-14

* BigQuery: skip Omni locations when extracting SQL queries

## 0.25.19 - 2025-11-14

* Redshift: support extraction of queries longer than 65,535 characters

## 0.25.18 - 2025-11-13

* Power BI: expand groups into individual users

## 0.25.17 - 2025-11-04

* Snowflake: add query_block to exclude specific sql patterns

## 0.25.16 - 2025-11-03

* Snowflake: remove duplicated queries, based on query_hash

## 0.25.15 - 2025-10-30

* Databricks: Add `http_path` mandatory field for databricks credentials

## 0.25.14 - 2025-10-28

* Removing unused dependency (google-cloud-storage)

## 0.25.13 - 2025-10-16

* Coalesce:
  * reduce pagination
  * retry once on ReadTimeout or ConnectionTimeout

## 0.25.12 - 2025-10-16

* Add a deprecation warning for Python versions below 3.10

## 0.25.11 - 2025-10-15

* Sigma: catch ReadTimeouts during queries extraction

## 0.25.10 - 2025-10-09

* Fix import

## 0.25.9 - 2025-10-09

* Snowflake: raise an exception when no database is available for extraction
* Databricks: raise an exception when no database is available for extraction
* BigQuery: raise an exception when no project is available for extraction

## 0.25.8 - 2025-10-09

* Count: extracting queries and canvas_loads

## 0.25.7 - 2025-10-07

* SqlServer: Ensure database consistency between query and engine

## 0.25.6 - 2025-10-06

* PowerBi: Support additional authentication methods

## 0.25.5 - 2025-10-06

* Snowflake: remove extraction of roles and grants

## 0.25.4 - 2025-10-02

* SqlServer: switch database to support clients running their instance on Azure

## 0.25.3 - 2025-10-01

* Sigma: sleep between sources requests to avoid rate limit errors

## 0.25.2 - 2025-09-30

* PowerBi: Support auth with private_key

## 0.25.1 - 2025-09-29

* Sigma: catch ReadTimeouts during elements extraction

## 0.25.0 - 2025-09-15

* Count: adding connector

## 0.24.57 - 2025-09-24

* Sigma:
  * fix pagination
  * remove redundant element lineages endpoint
  * extract data model sources

## 0.24.56 - 2025-09-24

* bump dependencies

## 0.24.55 - 2025-09-19

* Fix encoding in LocalStorage - force to utf-8

## 0.24.54 - 2025-09-18

* SqlServer: fix typo in the extraction query of schemas

## 0.24.53 - 2025-09-18

* Fix CSV field size to support running on Windows

## 0.24.52 - 2025-09-18

* SqlServer : improve extraction of users and technical owners

## 0.24.51 - 2025-09-17

* PowerBI : don't store sensitive data in activity events

## 0.24.50 - 2025-09-15

* SqlServer: support multiple databases in queries

## 0.24.49 - 2025-09-12

* Tableau: add option to bypass ssl certificate verification

## 0.24.48 - 2025-09-09

* SqlServer: handle hyphens in database name

## 0.24.47 - 2025-09-08

* SqlServer: extract SQL queries and lineage

## 0.24.46 - 2025-09-03

* Sigma: Added `HTTPStatus.FORBIDDEN` to the list of ignored errors

## 0.24.45 - 2025-08-27

* Sigma: Increasing pagination limit for Sigma extraction

## 0.24.44 - 2025-08-22

* Coalesce: do not skip nodes raising a 500 Server Error

## 0.24.43 - 2025-08-20

* SQLServer:
  * raise error when no database is left after filtering
  * use uppercase INFORMATION_SCHEMA for case-sensitive database compatibility

## 0.24.42 - 2025-08-19

* Strategy: exclude COLUMNS from extraction

## 0.24.41 - 2025-08-19

* Sigma: retry on 429 errors when fetching connection paths

## 0.24.40 - 2025-08-18

* SQLServer: fix database allowlist/blocklist filtering

## 0.24.39 - 2025-08-18

* Databricks:
  * Fix vanishing owner ID column for tables
  * Deduplicate lineage with SQL to reduce memory use

## 0.24.38 - 2025-08-07

* Uploader: Support US and EU zones

## 0.24.37 - 2025-08-06

* Sigma: extract data models, dataset sources and workbook sources

## 0.24.36 - 2025-08-04

* Sigma:
  * Refresh token before lineage extraction
  * Disregard 403 errors during lineage extraction

## 0.24.35 - 2025-07-29

* Coalesce - Fix pagination issue

## 0.24.34 - 2025-07-02

* SQLServer: multiple databases

## 0.24.33 - 2025-07-10

* Tableau - Add an option to skip fields ingestion

## 0.24.32 - 2025-07-02

* Salesforce reporting - extract report's metadata

## 0.24.31 - 2025-07-02

* Looker Studio: add an option to list users via a provided JSON file

## 0.24.30 - 2025-06-26

* Sigma: remove retry on timeout, decrease pagination for queries

## 0.24.29 - 2025-06-24

* Strategy: skip descriptions on ValueErrors

## 0.24.28 - 2025-06-20

* Snowflake: ignore private notebooks

## 0.24.27 - 2025-06-20

* Strategy: extract logical tables

## 0.24.26 - 2025-06-16

* Coalesce: increase _MAX_ERRORS client parameter

## 0.24.25 - 2025-06-12

* DBT: Fix API base url

## 0.24.24 - 2025-06-06

* Power BI: handle rate limit issues when extracting pages

## 0.24.23 - 2025-06-05

* Salesforce: print response's error message when authentication fails

## 0.24.22 - 2025-05-27

* Add retry for `Request.Timeout` on **ApiClient**

## 0.24.21 - 2025-05-26

* Looker Studio: add option to skip the extraction of view activity logs

## 0.24.20 - 2025-05-19

* Powerbi: allow custom api base and login url

## 0.24.19 - 2025-05-14

* Confluence: extract databases

## 0.24.18 - 2025-05-13

* Improve folder organisation for transformation tools

## 0.24.17 - 2025-05-13

* Strategy: fix dashboard URL format

## 0.24.16 - 2025-05-12

* Confluence: extract folders to complete the page hierarchy

## 0.24.15 - 2025-05-12

* Tableau: Add argument to skip columns extraction

## 0.24.14 - 2025-05-06

* Confluence: extract pages per space to allow additional filtering. by default, pages from archived or personal spaces are not extracted.

## 0.24.13 - 2025-05-05

* Rollback cloud-storage version as it's not compatible with Keboola

## 0.24.12 - 2025-05-05

* Redshift - fix query definition of materialized views

## 0.24.11 - 2025-05-05

* add support for Strategy (formerly MicroStrategy)

## 0.24.10 - 2025-04-30

* Tableau - skip warnings instead of raising an error

## 0.24.9 - 2025-04-16

* Introduce API client for **Coalesce**

## 0.24.8 - 2025-04-16

* Tableau - remove duplicates introduced by `offset` pagination

## 0.24.7 - 2025-04-07

* Tableau - switch from `cursor` to `offset` pagination to mitigate timeout issues

## 0.24.6 - 2025-04-03

* Domo - extract cards metadata by batch to prevent from hitting URL max length

## 0.24.5 - 2025-04-02

* bump dependencies: google-cloud-storage

## 0.24.4 - 2025-03-19

* Snowflake:
  * improve the list of ignored queries in the query history extraction
    * ignore the following query types : CALL, COMMENT, EXPLAIN, REFRESH_DYNAMIC_TABLE_AT_REFRESH_VERSION, REVOKE, TRUNCATE_TABLE, UNDROP
    * ignore queries with empty text
  * filter out schemas with empty names

## 0.24.3 - 2025-03-18

* Replace ThoughtSpot endpoint `/api/rest/2.0/report/liveboard` with `/api/rest/2.0/metadata/liveboard/data` following the deprecation of the CSV option

## 0.24.2 - 2025-03-17

* Rename Revamped Tableau Connector classes

## 0.24.1 - 2025-03-14

* Added support for Looker Studio

## 0.24.0 - 2025-03-10

* Remove legacy Tableau Connector

## 0.23.3 - 2025-02-19

* Snowflake : add --insecure-mode option to turn off OCSP checking

## 0.23.2 - 2025-02-17

* support page_size in Tableau extraction command

## 0.23.1 - 2025-02-10

* change command for Confluence from password to token to reflect better their documentation

## 0.22.6 - 2025-01-21

* bump dependencies: looker, databricks, deptry, ...

## 0.22.5 - 2025-01-09

* Databricks: validate and deduplicate lineage links

## 0.22.4 - 2025-01-08

* ThoughtSpot: extract answers

## 0.22.3 - 2024-12-10

* Databricks: extract lineage from system tables

## 0.22.2 - 2024-12-06

* Sigma: multithreading to retrieve lineage

## 0.22.1 - 2024-12-05

* Salesforce: deduplicate tables

## 0.22.0 - 2024-12-04

* Stop supporting python3.8

## 0.21.9 - 2024-12-04

* Tableau: fix handling of timeout retry

## 0.21.8 - 2024-11-26

* Redshift: improve deduplication of columns

## 0.21.7 - 2024-11-26

* Metabase: stop using deprecated table `view_log`

## 0.21.6 - 2024-11-22

* bump dependencies: ruff, setuptools

## 0.21.5 - 2024-11-20

* PostgreSQL: Fix schema extraction when owner is a role without login privilege

## 0.21.4 - 2024-11-20

* Uploader: Support environment variables as settings

## 0.21.3 - 2024-11-07

* Tableau: Fix metrics definition url

## 0.21.2 - 2024-11-06

* Adding fetch method for confluence client

## 0.21.1 - 2024-10-23

* Warning message to deprecate python < 3.9

## 0.21.0 - 2024-10-23

* Confluence: Added Confluence extractor

## 0.20.8 - 2024-10-19

* bump dependencies (minor and patches)

## 0.20.7 - 2024-10-18

* Metabase: fix `require_ssl` type in credentials

## 0.20.6 - 2024-10-15

* Tableau: include `site_id` in **workbooks** to build url

## 0.20.5 - 2024-10-09

* Redshift: enable extraction from a Redshift Serverless instance

## 0.20.4 - 2024-10-09

* Salesforce warehouse: `Labels` instead of `api_names` for columns

## 0.20.3 - 2024-10-03

* Looker: no longer extract `as_html` dashboard elements

## 0.20.2 - 2024-09-24

* Thoughtspot: Adding connector

## 0.20.1 - 2024-09-23

* Power BI: Improved client based on APIClient

## 0.20.0 - 2024-09-23

* Switch to Tableau revamped connector

## 0.19.9 - 2024-09-19

* Databricks: multithreading to retrieve column lineage

## 0.19.8 - 2024-09-18

* Metabase: Handle duplicate dashboards
* Snowflake: Exclude unnamed tables from extraction
* Bump dependencies: cryptography, setuptools

## 0.19.7 - 2024-09-05

* Metabase: Handle compatibility with older version

## 0.19.6 - 2024-09-03

* Metabase: Adding error handler on API call

## 0.19.5 - 2024-09-02

* Databricks/Salesforce: Remove deprecated client dependencies

## 0.19.4 - 2024-08-29

* Tableau Pulse: extract Metrics and Subscriptions

## 0.19.3 - 2024-08-27

- Sigma: Add SafeMode to SigmaClient

## 0.19.2 - 2024-08-23

- Reworked APIClient to unify client's behaviours

Impacted Technologies: Sigma, Soda, Notion

## 0.19.1 - 2024-08-23

* Domo: extract datasources via cards metadata endpoint

## 0.19.0 - 2024-08-21

* Breaking change Looker CLI:

`-u` and `--username` changed to `-c` `--client-id`

`-p` and `--password` changed to `-s` `--client-secret`

* Breaking change Metabase CLI:

`-u` and `--username` changed to `-u` `--user`


* Note: if you use environment variables you shouldn't be impacted

## 0.18.13 - 2024-08-19

* Qlik: improve measures extraction

## 0.18.12 - 2024-08-19

* Bumps: looker-sdk: 24, setuptools: 72

## 0.18.11 - 2023-08-14

* Linting and formatting with Ruff

## 0.18.10 - 2024-08-13

* Soda: Added Soda extractor (Castor-Managed integration only)

## 0.18.9 - 2024-08-12

* Notion: Added Notion extractor

## 0.18.8 - 2024-08-02

* Databricks: more reliable extraction of queries

## 0.18.7 - 2024-08-01

* Salesforce: extract table descriptions

## 0.18.6 - 2024-07-30

* BigQuery: introduce extended regions to extract missing queries

## 0.18.5 - 2024-07-17

* Salesforce: extract DeveloperName and tooling url

## 0.18.4 - 2024-07-16

* Fix environment variables assignments for credentials

## 0.18.3 - 2024-07-16

* bump dependencies (minor and patches)

## 0.18.2 - 2024-07-08

* Added StatusCode handling to SafeMode

## 0.18.1 - 2024-07-04

* Bump dependencies: numpy, setuptools, tableauserverclient

## 0.18.0 - 2024-07-03

* Dashboarding technologies : Reworked credentials using Pydantic

## 0.17.5 - 2024-07-03

* Snowflake, Synapse, Redshift: Remove default_value from the extracted column

## 0.17.4 - 2024-07-03

* Sigma: Add `input-table`, `pivot-table` and `viz` in the list of supported **Elements**

## 0.17.3 - 2024-06-24

* Databricks: extract tags for tables and column

## 0.17.2 - 2024-06-14

* Uploader: support multipart

## 0.17.1 - 2024-06-12

* Databricks: extract table source links

## 0.17.0 - 2024-06-10

* Uploader: redirect to the proxy, replace credentials with token

## 0.16.15 - 2024-06-07

* Tableau: extract database_name for CustomSQLTables

## 0.16.14 - 2024-06-06

* Snowflake: Extract SQL user defined function

## 0.16.13 - 2024-06-05

* Tableau: extract database_name for tables

## 0.16.12 - 2024-06-04

* Databricks: Extract lineage

## 0.16.11 - 2024-06-03

* Tableau: add extra fields to optimise storage

## 0.16.10 - 2024-05-30

* Salesforce: extract sobjects Label as table name

## 0.16.9 - 2024-05-28

* Tableau: extract only fields that are necessary

## 0.16.8 - 2024-05-21

* Add compatibility with python 3.12
* Looker: Bump looker-sdk and refactor client

## 0.16.7 - 2024-05-16

* Databricks: allow no emails on user

## 0.16.6 - 2024-05-14

* Introducing the revamped connector for Tableau

## 0.16.5 - 2024-04-25

* Salesforce: remove DeploymentStatus from EntityDefinition query

## 0.16.4 - 2024-04-25

* Salesforce: extract sobjects and fields

## 0.16.3 - 2024-04-24

* Databricks: Extract table owners

## 0.16.2 - 2024-04-09

* PowerBI: Extract pages from report

## 0.16.1 - 2024-04-02

* Systematically escape nul bytes on CSV write

## 0.16.0 - 2024-03-26

* Use pydantic v2

## 0.15.4 - 2024-03-25

* Pagination: Fix behavior when next page token is missing

## 0.15.3 - 2024-03-08

* Sigma: Regenerate token when expired

## 0.15.2 - 2024-03-01

* DBT: Add host base URL, use of BaseSettings for DbtCredentials

## 0.15.1 - 2024-03-06

* Salesforce: extract dashboard components

## 0.15.0 - 2024-03-01

* Support Databricks Unity Catalog extraction

## 0.14.14 - 2024-02-27

* Salesforce: Fix on salesforce folders URL

## 0.14.13 - 2024-02-15

* Domo client: Handles cases where datasources aren't linked to any cards

## 0.14.12 - 2024-02-13

* Domo client: No longer raise 400 exception upon API calls

## 0.14.11 - 2024-02-13

* BigQuery client: Use partitioned `creation_time` instead of `start_time`

## 0.14.10 - 2024-02-08

* Metabase ApiClient: Remove GET /api/dashboard that is deprecated

## 0.14.9 - 2024-02-07

* Add support for python 3.11

## 0.14.8 - 2024-02-06

* Salesforce client: extracting folders

## 0.14.7 - 2024-02-05

* Domo: ignore 404 errors on datasources API endpoint

## 0.14.6 - 2024-01-31

* Bump dependencies

## 0.14.5 - 2024-01-31

* Allow support of external lineage for non-generic technologies

## 0.14.4 - 2024-01-30

* Salesforce client: Renaming salesforce viz to salesforce reporting

## 0.14.3 - 2024-01-29

* Domo: enhance pages with card's datasources to support direct tables lineage

## 0.14.2 - 2024-01-25

* Salesforce client: Methods to extract users, dashboards and reports

## 0.14.1 - 2024-01-24

* Add sensitive metadata information to credentials dataclass

## 0.14.0 - 2024-01-24

* Adding Salesforce client

## 0.13.0 - 2024-01-22

* Support MySQL catalog extraction

## 0.12.3 - 2024-01-16

* Metabase: renaming of dashboard_cards for Metabase 0.48

## 0.12.2 - 2023-12-27

* Metabase: Align postgres connection to postgres connector

## 0.12.1 - 2023-12-27

* Tableau: replace luid with id during dashboards extraction

## 0.12.0 - 2023-12-18

* SQL Server: extract catalog

## 0.11.3 - 2023-12-21

* Metabase: Support postgres connection via SSL

## 0.11.2 - 2023-12-20

* Extract: remove null byte characters

## 0.11.1 - 2023-12-20

* Fixed bug with jitter argument in Retry class and added field validations

## 0.11.0 - 2023-12-18

* Tableau: extract dashboards

## 0.10.2 - 2023-12-13

* Redshift: Handle rows with mixed encodings

## 0.10.1 - 2023-12-04

* Domo: fix pagination

## 0.10.0 - 2023-11-28

* Looker : extract all Looker Explores, even if unused in Dashboards

## 0.9.2 - 2023-11-23

* Looker : remove deprecated all_looks parameter

## 0.9.1 - 2023-11-22

* Redshift : filter out queries exceeding 65535 char

## 0.9.0 - 2023-11-20

* Snowflake : Add key-pair authentication

## 0.8.1 - 2023-11-15

* Add a logging option to log to stdout

## 0.8.0 - 2023-11-09

* Stream **Looker** Looks and Dashboards directly into their destination files

## 0.7.8 - 2023-11-02

* Rollback `escapechar` in csv options

## 0.7.7 - 2023-10-30

* Add `escapechar` in csv de-serialization

## 0.7.6 - 2023-10-26

* Fetch Domo audits up to yesterday date

## 0.7.5 - 2023-10-26

* Add `escapechar` in csv serialisation

## 0.7.4 - 2023-10-23

* Pick the most recent sharded tables in `BigQuery`

## 0.7.3 - 2023-10-19

* Add retry mechanism to LookerClient when multithreading

## 0.7.2 - 2023-10-19

* pycryptodome moved as an optional dependency for extras: metabase and all

## 0.7.1 - 2023-10-04

* Fix thread pool size verification

## 0.7.0 - 2023-10-02

* Add option to fetch Looker Looks & Dashboards per folder

## 0.6.3 - 2023-10-02

* Add refreshing mechanism for Domo authentication tokens

## 0.6.2 - 2023-09-29

* Update field_size_limit in CSVFormatter

## 0.6.1 - 2023-09-25

* Add support for Domo

## 0.6.0 - 2023-09-25

* Move msal dependencies to powerbi extra

## 0.5.10 - 2023-09-25

* Retrieve column_id instead of object_id for Snowflake column tags

## 0.5.9 - 2023-09-21

* Add column tags for Snowflake

## 0.5.8 - 2023-09-19

* Remove non-used dependencies
* Fix some import in tests
* Clean pyproject.toml
* Add deptry config

## 0.5.7 - 2023-08-17

* Update column data type validator

## 0.5.6 - 2023-08-10

* Use latest version of certifi (2023.7.22)

## 0.5.5 - 2023-08-07

* Linting with flakeheaven

## 0.5.4 - 2023-08-01

* Add support for Looker's `Users Attributes`

## 0.5.3 - 2023-07-27

* Add support for PowerBI's `Activity Events`

## 0.5.2 - 2023-07-12

* Fix Metabase DbClient url

## 0.5.1 - 2023-07-03

* Add support for Looker's `ContentViews`

## 0.5.0 - 2023-06-28

* Stop supporting python3.7

## 0.4.1 - 2023-06-27

* Fix on Sigma elements extraction
* Fix BigQuery dataset extraction
* Fix the File Checker for View DDL file

## 0.4.0 - 2023-06-12

* Added support for Sigma

## 0.3.8 - 2023-05-02

* Added support for PowerBI datasets and fields

## 0.3.7 - 2023-04-28

* Warning message to deprecate python < 3.8

## 0.3.6 - 2023-04-24

* Update enum keys for Metabase credentials

## 0.3.5 - 2023-04-07

* Extract metadata from successful dbt runs only

## 0.3.4 - 2023-04-05

* Enhance uploader to support `QUALITY` files

## 0.3.3 - 2023-04-04

* Tableau : Improve Table <> Datasource lineage

## 0.3.2 - 2023-04-04

* Allow COPY statements from Snowflake

## 0.3.1 - 2023-03-30

* Improved Field extraction in Tableau

## 0.3.0 - 2023-03-29

* Added Tableau datasource and field integration

## 0.2.3 - 2023-03-17

* Verify required admin permissions for Looker extraction

## 0.2.2 - 2023-03-13

* Constraint `setuptools` explicitly added

## 0.2.1 - 2023-02-23

* Constrain `google-cloud-bigquery` dependency below yanked 3.0.0

## 0.2.0 - 2023-02-13

* Add connector for dbt-cloud

## 0.1.2 - 2023-02-08

* Enhance **Looker** extraction of dashboard filters and groups with roles

## 0.1.1 - 2023-02-06

* Add **Looker** support to extract `groups`-related assets
* Enhance **Looker** extraction of dashboard elements and users

## 0.1.0 - 2023-01-17

* Upgrade to Python 3.8
* Upgrade dependencies

## 0.0.44 - 2023-01-02

* Introduce new extractor for visualization tool **PowerBi** with support for
  * `reports`
  * `dashboards`
  * `metadata`

## 0.0.43 - 2022-12-21

* Update package dependencies

## 0.0.42 - 2022-11-25

* Improve pagination

## 0.0.41 - 2022-10-26

* Tableau: Optional `site-id` argument for Tableau Server users

## 0.0.40 - 2022-10-25

* Fix command `file_check`

## 0.0.39 - 2022-10-24

* Fix `FileChecker` template for `GenericWarehouse.view_ddl`

## 0.0.38 - 2022-10-17

* Snowflake: extract `warehouse_size`

## 0.0.37 - 2022-10-14

* Allow to skip "App size exceeded" error while fetching Qlik measures
* Fix missing arguments `warehouse` and `role` passing for script `extract_snowflake`

## 0.0.36 - 2022-10-13

* Patch error in Looker explore names

## 0.0.35 - 2022-10-12

* Add safe mode to **Looker**

## 0.0.34 - 2022-10-11

* Fix extras dependencies

## 0.0.33 - 2022-10-10

* Migrate package generation to poetry

## 0.0.32 - 2022-10-07

* Improved logging

## 0.0.31 - 2022-10-05

* Safe mode for bigquery and file logger

## 0.0.30 - 2022-09-20

* Add **Qlik** support to extract `connections` assets

## 0.0.29 - 2022-08-31

* Switch to engine's connect for database connections

## 0.0.28 - 2022-07-29

* Widen dependencies ranges

## 0.0.27 - 2022-07-28

* Improve support for Qlik `measures` and `lineage` and drop extraction of `qvds`

## 0.0.26 - 2022-07-22

* Add **Qlik** support to extract `measures` assets

## 0.0.25 - 2022-07-04

* Add **Qlik** support to extract `qvds` and `lineage` assets

## 0.0.24 - 2022-06-30

* Allow to use `all_looks` endpoint to retrieve looker Looks for param or env variable.

## 0.0.23 - 2022-06-29

* Allow to change Looker api timeout through param or env variable.

## 0.0.22 - 2022-06-20

* Introduce new extractor for visualization tool **Qlik** with support for
  * `spaces`
  * `users`
  * `apps`

## 0.0.21 - 2022-06-09

* Fix typo in Snowflake schema extract query

## 0.0.20 - 2022-06-08

* Fetch only distinct schemas in Snowflake warehouse

## 0.0.19 - 2022-05-30

* Use versions with range to ease dependency resolution for python 3.7 to 3.10

## 0.0.18 - 2022-05-19

* Enhance the file checker to search for prefixed files

## 0.0.17 - 2022-05-18

* Add retry for mode analytics

## 0.0.16 - 2022-05-18

* Add options to the pager:
  * `start_page`: to start pagination at another index (default to 1)
  * `stop_strategy`: to use different strategy to stop pagination (default to EMPTY_PAGE)

## 0.0.15 - 2022-05-09

* Skip snowflake columns with no name

## 0.0.14 - 2022-05-09

* Add missing metabase dependencies on Psycopg2

## 0.0.13 - 2022-05-06

* Remove top-level imports to isolate modules with different extra dependencies

## 0.0.12 - 2022-05-06

* Improved the file checker to detect repeated quotes in CSV.

## 0.0.11 - 2022-05-02

* Fix import error in `file_checker` script

## 0.0.10 - 2022-04-27

* Snowflake: discard 11 more `query_type` values when fetching queries

## 0.0.9 - 2022-04-13

* allow Looker parameters `CASTOR_LOOKER_TIMEOUT_SECOND` and `CASTOR_LOOKER_PAGE_SIZE` to be passed through environment
variables
* fix import paths in `castor_extractor/commands/upload.py` script
* use `storage.Client.from_service_account_info` when `credentials` is a dictionary in `uploader/upload.py`

## 0.0.8 - 2022-04-07

* Fix links to documentation in the README

## 0.0.7 - 2022-04-05

* Fix dateutil import issue

## 0.0.6 - 2022-04-05

First version of Castor Extractor, including:

* Warehouse assets extraction
  * BigQuery
  * Postgres
  * Redshift
  * Snowflake

* Visualization assets extraction
  * Looker
  * Metabase
  * Mode Analytics
  * Tableau

* Utilities
  * Uploader to cloud-storage
  * File Checker (for generic metadata)
