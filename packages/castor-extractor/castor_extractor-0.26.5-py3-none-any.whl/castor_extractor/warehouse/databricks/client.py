import logging

from ...utils import mapping_from_rows
from ..abstract import TimeFilter
from .api_client import DatabricksAPIClient
from .credentials import DatabricksCredentials
from .enums import TagEntity
from .format import DatabricksFormatter
from .sql_client import DatabricksSQLClient
from .types import TablesColumns

logger = logging.getLogger(__name__)

_THREADS_COLUMN_LINEAGE = 2
_THREADS_TABLE_LINEAGE = 10


class DatabricksClient:
    """Databricks Client"""

    def __init__(
        self,
        credentials: DatabricksCredentials,
        db_allowed: set[str] | None = None,
        db_blocked: set[str] | None = None,
        has_table_tags: bool = False,
        has_column_tags: bool = False,
    ):
        self.api_client = DatabricksAPIClient(
            credentials=credentials,
            db_allowed=db_allowed,
            db_blocked=db_blocked,
        )
        self.sql_client = DatabricksSQLClient(
            credentials=credentials,
            has_table_tags=has_table_tags,
            has_column_tags=has_column_tags,
        )

        self.formatter = DatabricksFormatter()

    @staticmethod
    def name() -> str:
        return "Databricks"

    @staticmethod
    def _match_table_with_user(table: dict, user_mapping: dict) -> dict:
        """Matches the table's owner email to an ID, or None if not found."""
        table_owner_email = table.get("owner_email")
        owner_external_id = (
            user_mapping.get(table_owner_email) if table_owner_email else None
        )
        return {**table, "owner_external_id": owner_external_id}

    @staticmethod
    def _get_user_mapping(users: list[dict]) -> dict:
        return {
            **mapping_from_rows(users, "email", "id"),
            **mapping_from_rows(users, "user_name", "id"),
        }

    def schemas(self, databases: list[dict]) -> list[dict]:
        return self.api_client.schemas(databases)

    def databases(self) -> list[dict]:
        return self.api_client.databases()

    def tables_and_columns(
        self, schemas: list[dict], users: list[dict]
    ) -> TablesColumns:
        """
        Get the databricks tables & columns leveraging the unity catalog API
        """
        tables: list[dict] = []
        columns: list[dict] = []
        user_mapping = self._get_user_mapping(users)
        table_tags = self.sql_client.get_tags_mapping(TagEntity.TABLE)
        column_tags = self.sql_client.get_tags_mapping(TagEntity.COLUMN)
        for schema in schemas:
            t_to_add, c_to_add = self.api_client.tables_columns_of_schema(
                schema=schema,
                table_tags=table_tags,
                column_tags=column_tags,
            )
            t_with_owner = [
                self._match_table_with_user(table, user_mapping)
                for table in t_to_add
            ]
            tables.extend(t_with_owner)
            columns.extend(c_to_add)
        return tables, columns

    def queries(self, time_filter: TimeFilter | None = None) -> list[dict]:
        return self.api_client.queries(time_filter)

    def users(self) -> list[dict]:
        return self.api_client.users()

    def view_ddl(self, schemas: list[dict]) -> list[dict]:
        return self.api_client.view_ddl(schemas)
