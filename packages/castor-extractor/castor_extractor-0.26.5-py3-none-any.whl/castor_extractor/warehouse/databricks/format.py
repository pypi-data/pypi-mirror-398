import logging
from datetime import datetime

from .types import TablesColumns
from .utils import build_path

logger = logging.getLogger(__name__)

EXCLUDED_DATABASES = {"system"}
EXCLUDED_SCHEMAS = {"information_schema", "default"}

TABLE_URL_TPL = "{host}explore/data/{catalog_name}/{schema_name}/{table_name}?o={workspace_id}"

TagMapping = dict[str, list[str]]


def _to_datetime_or_none(time_ms: int | None) -> datetime | None:
    """return time in ms as datetime or None"""
    if not time_ms:
        return None
    return datetime.fromtimestamp(time_ms / 1000.0)


def _table_payload(
    schema: dict,
    table: dict,
    host: str,
    workspace_id: str,
    tags: TagMapping,
) -> dict:
    """
    Prepares the table payload. This also includes a source link which is built
    here using the host and workspace_id.
    """
    url = TABLE_URL_TPL.format(
        host=host,
        catalog_name=table["catalog_name"],
        schema_name=table["schema_name"],
        table_name=table["name"],
        workspace_id=workspace_id,
    )

    keys = ["catalog_name", "schema_name", "name"]
    path = build_path(table, keys)

    return {
        "description": table.get("comment"),
        "id": table["table_id"],
        "owner_email": table.get("owner"),
        "schema_id": f"{schema['id']}",
        "table_name": table["name"],
        "tags": tags.get(path, []),
        "type": table.get("table_type"),
        "url": url,
    }


def _column_path(table: dict, column: dict) -> str:
    keys = ["catalog_name", "schema_name", "name"]
    table_path = build_path(table, keys)
    column_name = column["name"]
    return f"{table_path}.{column_name}"


def _column_payload(
    table: dict,
    column: dict,
    tags: TagMapping,
) -> dict:
    path = _column_path(table, column)
    return {
        "column_name": column["name"],
        "data_type": column["type_name"],
        "description": column.get("comment"),
        "id": f"`{table['table_id']}`.`{column['name']}`",
        "ordinal_position": column["position"],
        "table_id": table["table_id"],
        "tags": tags.get(path, []),
    }


class DatabricksFormatter:
    """
    Helper functions.
    Format the response in the format to be exported as csv
    """

    @staticmethod
    def format_database(raw_databases: list[dict]) -> list[dict]:
        databases = []
        for catalog in raw_databases:
            name = catalog["name"]
            if name in EXCLUDED_DATABASES:
                continue
            db = {
                "id": name,
                "database_name": name,
            }
            databases.append(db)
        return databases

    @staticmethod
    def format_schema(raw_schemas: list[dict], database: dict) -> list[dict]:
        schemas = []
        for schema in raw_schemas:
            if schema["name"] in EXCLUDED_SCHEMAS:
                continue
            sc = {
                "id": schema["full_name"],
                "database_id": database["id"],
                "schema_name": schema["name"],
                "description": schema.get("comment"),
                "tags": [],
            }
            schemas.append(sc)
        return schemas

    @staticmethod
    def format_table_column(
        raw_tables: list[dict],
        schema: dict,
        host: str,
        workspace_id: str,
        table_tags: TagMapping,
        column_tags: TagMapping,
    ) -> TablesColumns:
        tables = []
        columns = []
        if not raw_tables:
            return [], []
        for table in raw_tables:
            t = _table_payload(schema, table, host, workspace_id, table_tags)
            tables.append(t)
            if not table.get("columns"):
                continue
            for column in table["columns"]:
                c = _column_payload(table, column, column_tags)
                columns.append(c)

        return tables, columns

    @staticmethod
    def format_lineage(timestamps: dict) -> list[dict]:
        lineage: list[dict] = []
        for link, timestamp in timestamps.items():
            parent_path, child_path = link
            link_ = {
                "parent_path": parent_path,
                "child_path": child_path,
                "timestamp": timestamp,
            }
            lineage.append(link_)
        return lineage

    @staticmethod
    def format_query(raw_queries: list[dict]) -> list[dict]:
        queries = []
        for q in raw_queries:
            if not q["query_text"]:
                continue
            start_time = _to_datetime_or_none(q.get("query_start_time_ms"))
            end_time = _to_datetime_or_none(q.get("query_end_time_ms"))
            query = {
                "query_id": q["query_id"],
                "database_id": None,
                "database_name": None,
                "schema_name": None,
                "query_text": q["query_text"],
                "user_id": q["user_id"],
                "user_name": q.get("user_name"),
                "start_time": start_time,
                "end_time": end_time,
            }
            queries.append(query)
        return queries

    @staticmethod
    def _primary(emails: list[dict]) -> str | None:
        """helper function to select a unique email"""
        if not emails:
            return None
        for email in emails:
            if email.get("primary", False):
                return email["value"]
        return emails[0]["value"]

    def _email(self, user: dict) -> str | None:
        emails = user.get("emails")
        return self._primary(emails) if emails else None

    def format_user(self, raw_users: list[dict]) -> list[dict]:
        users = []
        for user in raw_users:
            users.append(
                {
                    "id": user["id"],
                    "email": self._email(user),
                    "first_name": None,
                    "last_name": user.get("displayName") or user["userName"],
                    "user_name": user["userName"],
                }
            )
        return users

    @staticmethod
    def format_view_ddl(tables: list[dict], schema: dict) -> list[dict]:
        view_ddl: list[dict] = []
        if not tables:
            return view_ddl
        for table in tables:
            if not table.get("view_definition"):
                continue
            view_ddl.append(
                {
                    "database_name": schema["database_id"],  # db id = name
                    "schema_name": schema["schema_name"],
                    "view_name": table["name"],
                    "view_definition": table["view_definition"],
                }
            )

        return view_ddl
