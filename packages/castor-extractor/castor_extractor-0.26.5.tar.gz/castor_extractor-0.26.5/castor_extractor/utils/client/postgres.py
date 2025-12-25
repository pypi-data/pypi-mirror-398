from .abstract import SqlalchemyClient
from .uri import uri_encode

POSTGRES_URI = "postgresql://{user}:{password}@{host}:{port}/{database}"

DEFAULT_PORT = 5432


class PostgresClient(SqlalchemyClient):
    """Postgres client"""

    @staticmethod
    def name() -> str:
        return "PostgreSQL"

    def _engine_options(self, credentials: dict) -> dict:
        return {"connect_args": {"sslmode": "prefer"}}

    def _build_uri(self, credentials: dict) -> str:
        keys = ("user", "password", "host", "port", "database")
        assert all(k in credentials for k in keys)
        return POSTGRES_URI.format(
            user=credentials["user"],
            password=uri_encode(credentials["password"]),
            host=credentials["host"],
            port=credentials.get("port") or DEFAULT_PORT,
            database=credentials["database"],
        )
