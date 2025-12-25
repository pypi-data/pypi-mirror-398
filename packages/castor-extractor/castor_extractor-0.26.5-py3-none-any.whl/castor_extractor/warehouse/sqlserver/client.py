import logging
from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from ...utils import SqlalchemyClient, uri_encode
from ..abstract import ExtractionQuery

logger = logging.getLogger(__name__)

SERVER_URI = "{user}:{password}@{host}:{port}"
MSSQL_URI = f"mssql+pymssql://{SERVER_URI}"
DEFAULT_PORT = 1433

_KEYS = ("user", "password", "host", "port")

_SYSTEM_DATABASES = (
    "DBAdmin",
    "dbaTools",
    "master",
    "model",
    "msdb",
    "tempdb",
)


def _check_key(credentials: dict) -> None:
    for key in _KEYS:
        if key not in credentials:
            raise KeyError(f"Missing {key} in credentials")


class MSSQLClient(SqlalchemyClient):
    """Microsoft Server SQL client"""

    @staticmethod
    def name() -> str:
        return "MSSQL"

    def _engine_options(self, credentials: dict) -> dict:
        return {}

    def _build_uri(self, credentials: dict) -> str:
        _check_key(credentials)
        uri = MSSQL_URI.format(
            user=credentials["user"],
            password=uri_encode(credentials["password"]),
            host=credentials["host"],
            port=credentials.get("port") or DEFAULT_PORT,
        )
        return uri

    def _connect_to_database(self, database: str | None) -> Connection:
        """
        To support SQL Server running on Azure, we must change the engine's
        URI depending on the case:
        - URI/database for database-scoped queries
        - URI otherwise
        https://learn.microsoft.com/en-us/sql/t-sql/language-elements/use-transact-sql?view=sql-server-2017#database_name
        https://github.com/dbeaver/dbeaver/issues/5258
        """
        database_uri = f"{self._uri}/{database}" if database else self._uri
        self._engine = create_engine(database_uri, **self._options)
        try:
            return self.connect()
        except Exception:
            logger.error(f"Failed to connect to database {database or ''}")
            raise

    def execute(self, query: ExtractionQuery) -> Iterator[dict]:
        """
        Re-implements the SQLAlchemyClient execute function to ensure we consume
        the cursor before calling connection.close() as it wipes out the data
        otherwise
        """
        database = query.database
        connection = self._connect_to_database(database)
        try:
            proxy = connection.execute(text(query.statement), query.params)
            results = list(self._process_result(proxy))
            yield from results
        except Exception:
            logger.error(
                f"Failed to execute query in database {database or ''}"
            )
            raise
        finally:
            self.close()

    def get_databases(self) -> list[str]:
        result = self.execute(
            ExtractionQuery("SELECT name FROM sys.databases", {})
        )
        return [
            row["name"]
            for row in result
            if row["name"] not in _SYSTEM_DATABASES
        ]

    def _has_access(self, name: str, object_type: str, permission: str) -> bool:
        query_text = f"""
            SELECT
            HAS_PERMS_BY_NAME('{name}', '{object_type}', '{permission}')
            AS has_permission
        """
        query = ExtractionQuery(query_text, dict())
        result = next(self.execute(query))
        return result["has_permission"] == 1

    def _has_table_read_access(self, database: str, table_name: str) -> bool:
        """
        Check whether we have READ access to the given table
        """
        return self._has_access(
            name=f"[{database}].{table_name}",
            object_type="OBJECT",
            permission="SELECT",
        )

    def _has_view_database_state(self, database: str) -> bool:
        """
        Check whether we have VIEW DATABASE STATE permissions, which
        is necessary to fetch data from the Query Store
        """
        return self._has_access(
            name=database,
            object_type="DATABASE",
            permission="VIEW DATABASE STATE",
        )

    def _has_query_store(self, database: str) -> bool:
        """
        Checks whether the Query Store is activated on this database.
        This is required to extract the SQL queries history.
        https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store?view=sql-server-ver17"""
        sql = f"""
        SELECT
            desired_state
        FROM
            [{database}].sys.database_query_store_options
        """
        query = ExtractionQuery(
            statement=sql,
            params={},
            database=database,
        )
        # 2 = READ_WRITE, which means the Query Store is activated
        return next(self.execute(query))["desired_state"] == 2

    def has_queries_permissions(self, database: str) -> bool:
        """
        Verify that we have the required permissions to extract
        query history and view object definitions (DDL).

        This check ensures:
        - Query Store is enabled on the database.
        - We have the VIEW DATABASE STATE permissions
        - We have read access to the relevant system tables.
        """

        tables = (
            # SQL queries
            "sys.query_store_plan",
            "sys.query_store_query",
            "sys.query_store_query_text",
            "sys.query_store_runtime_stats",
            # views DDL
            "sys.schemas",
            "sys.sql_modules",
            "sys.views",
        )

        has_permissions = True
        for table in tables:
            if not self._has_table_read_access(database, table):
                logger.info(f"Missing READ permission on {database}.{table}")
                has_permissions = False

        if not self._has_view_database_state(database):
            logger.info(f"Missing VIEW DATABASE STATE in database {database}")
            has_permissions = False

        if not self._has_query_store(database):
            logger.info(f"Query Store is not activated in database {database}")
            has_permissions = False

        return has_permissions
