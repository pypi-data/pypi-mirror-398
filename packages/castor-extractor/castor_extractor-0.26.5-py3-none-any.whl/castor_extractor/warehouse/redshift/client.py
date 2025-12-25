import logging
from collections.abc import Iterator

from psycopg2 import extensions  # type: ignore
from sqlalchemy.engine import Connection, ResultProxy

from ...utils import SqlalchemyClient, decode_when_bytes, uri_encode

REDSHIFT_URI = "redshift+psycopg2://{user}:{password}@{host}:{port}/{database}"

DEFAULT_PORT = 5439

logger = logging.getLogger(__name__)


class RedshiftClient(SqlalchemyClient):
    """redshift client"""

    @staticmethod
    def name() -> str:
        return "Redshift"

    def _set_binary_connection(self) -> None:
        """
        Get the underlying psycopg2 connection and
        set the connection to BINARY mode
        """
        assert self._connection, "Connection missing"
        conn = self._connection.connection.connection
        extensions.register_type(extensions.BYTES, conn)

    def connect(self) -> Connection:
        connection = super().connect()
        self._set_binary_connection()
        return connection

    @staticmethod
    def _process_result(proxy: ResultProxy) -> Iterator[dict]:
        """
        Some clients using redshift have rows with mixed encoding, this
        function discard those problematics rows.
        """
        total_rows, decode_errors_count = 0, 0
        for row in proxy:
            total_rows += 1
            try:
                yield {
                    key: decode_when_bytes(value)
                    for key, value in dict(row).items()
                }
            except UnicodeDecodeError:
                decode_errors_count += 1
                continue

        if decode_errors_count > 0:
            logger.info(
                f"{decode_errors_count} UnicodeDecodeError on {total_rows} rows"
            )

    def _engine_options(self, credentials: dict) -> dict:
        return {"connect_args": {"sslmode": "verify-ca"}}

    def _build_uri(self, credentials: dict) -> str:
        return REDSHIFT_URI.format(
            user=credentials["user"],
            password=uri_encode(credentials["password"]),
            host=credentials["host"],
            port=credentials.get("port") or DEFAULT_PORT,
            database=credentials["database"],
        )
