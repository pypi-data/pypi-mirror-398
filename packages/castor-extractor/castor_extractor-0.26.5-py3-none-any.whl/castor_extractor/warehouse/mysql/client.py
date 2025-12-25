from ...utils import SqlalchemyClient, uri_encode

SERVER_URI = "{user}:{password}@{host}:{port}"
MYSQL_URI = f"mysql+pymysql://{SERVER_URI}"
DEFAULT_PORT = 3306

_REQUIRED_KEYS = ("user", "password", "host")


def _check_required_keys(credentials: dict) -> None:
    for key in _REQUIRED_KEYS:
        if key not in credentials:
            raise KeyError(f"Missing {key} in credentials")


class MySQLClient(SqlalchemyClient):
    """MySQL client"""

    @staticmethod
    def name() -> str:
        return "MySQL"

    def _engine_options(self, credentials: dict) -> dict:
        return {}

    def _build_uri(self, credentials: dict) -> str:
        _check_required_keys(credentials)
        uri = MYSQL_URI.format(
            user=credentials["user"],
            password=uri_encode(credentials["password"]),
            host=credentials["host"],
            port=credentials.get("port") or DEFAULT_PORT,
        )
        return uri
