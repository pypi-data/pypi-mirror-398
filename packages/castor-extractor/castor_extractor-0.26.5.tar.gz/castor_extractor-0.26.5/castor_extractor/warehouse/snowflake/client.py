import logging
import re
from enum import Enum

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from sqlalchemy.engine import Connection

from ...utils import SqlalchemyClient, to_string_array, uri_encode

SNOWFLAKE_URI = "snowflake://{user}:{password}@{account}/?application=castor"
PK_URI = "snowflake://{user}:@{account}/?application=castor"
PUBLIC_ROLE = "PUBLIC"

logger = logging.getLogger(__name__)


def _scalar(connection: Connection, query: str) -> str | None:
    """returns the first column of the first row, None if no row"""
    scalar = connection.execute(query).scalar()
    return None if scalar is None else str(scalar)


class UseResource(Enum):
    """resources using the USE syntax"""

    ROLE = "ROLE"
    WAREHOUSE = "WAREHOUSE"


def use(connection: Connection, resource: UseResource, name: str):
    """
    USE ROLE/WAREHOUSE do not accept SQL parameter substitution
        we do a sanity check prior to using it
    DON'T COPY THIS CODE FOR ANOTHER PURPOSE
    """
    target = resource.value
    if not re.fullmatch(r"[\w_-]+", name):
        raise NameError(f"{target} name invalid {name}")
    command = f'USE {target} "{name}"'
    logger.info(f"executing {command}")
    connection.execute(command)


def find_role(connection: Connection) -> str:
    """Finds available role within Snowflake environment"""
    current = _scalar(connection, "SELECT CURRENT_ROLE()")
    if current and current.upper() != PUBLIC_ROLE:
        logger.info(f"Role is already set: {current}")
        return current

    role = _first_non_public_role(connection)
    logger.info(f"Using first available role: {role}")
    return role


def find_warehouse(connection: Connection) -> str:
    """Finds available warehouse within Snowflake environment"""
    current = _scalar(connection, "SELECT CURRENT_WAREHOUSE()")
    if current:
        logger.info(f"Warehouse is already set: {current}")
        return current

    warehouse = _scalar(connection, "SHOW WAREHOUSES")
    if not warehouse:
        raise ConnectionError("no warehouse available")
    logger.info(f"Using first available warehouse: {warehouse}")
    return warehouse


def _first_non_public_role(connection: Connection) -> str:
    """fetch the first non public role granted to the user"""
    raw = _scalar(connection, "SELECT CURRENT_AVAILABLE_ROLES()")
    if not raw:
        raise ConnectionError("error at fetching granted roles")
    logger.info(f"available roles {raw}")
    parsed = to_string_array(raw)
    granted = {r.upper() for r in parsed} - {PUBLIC_ROLE}
    if not granted:
        raise ConnectionError("missing non public role")
    return next(iter(granted))


def _private_key(private_key: str | None) -> bytes | None:
    if not private_key:
        return None

    p_key = serialization.load_pem_private_key(
        bytes(private_key, "utf-8"), password=None, backend=default_backend()
    )

    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return pkb


class SnowflakeClient(SqlalchemyClient):
    """snowflake client"""

    # hide information message from the connectors
    logging.getLogger("snowflake.connector").setLevel(logging.WARNING)

    def __init__(
        self,
        credentials: dict,
        warehouse: str | None = None,
        role: str | None = None,
    ):
        self.private_key = _private_key(credentials.get("private_key"))
        self.insecure_mode = credentials.get("insecure_mode", False)
        super().__init__(credentials)
        self._role = role
        self._warehouse = warehouse

    @staticmethod
    def name() -> str:
        return "Snowflake"

    def _engine_options(self, credentials: dict) -> dict:
        """
        Sets the engine options.
        * `insecure_mode` = True turns off OCSP checking.
            See https://community.snowflake.com/s/article/How-to-turn-off-OCSP-checking-in-Snowflake-client-drivers
        * `private_key` = Snowflake private key for key pair authentication.
            See https://docs.snowflake.com/en/user-guide/key-pair-auth
        """
        connection_args: dict = dict()

        if self.insecure_mode:
            connection_args["insecure_mode"] = True

        if self.private_key:
            connection_args["private_key"] = self.private_key

        return {"connect_args": connection_args}

    def _build_uri(self, credentials: dict) -> str:
        if self.private_key:
            return PK_URI.format(
                account=credentials["account"],
                user=credentials["user"],
            )
        return SNOWFLAKE_URI.format(
            user=credentials["user"],
            password=uri_encode(credentials["password"]),
            account=credentials["account"],
        )

    def connection(self) -> Connection:
        """Authenticate to snowflake instance"""
        return super().connect()

    def role(self, connection: Connection) -> None:
        """check and set role"""
        if self._role:
            logger.info(f"Role was provided in arguments: {self._role}")
            use(connection, UseResource.ROLE, self._role)
            return

        role = find_role(connection)
        use(connection, UseResource.ROLE, role)

    def warehouse(self, connection: Connection):
        """check and set warehouse"""
        if self._warehouse:
            logger.info(
                f"Warehouse was provided in arguments: {self._warehouse}",
            )
            use(connection, UseResource.WAREHOUSE, self._warehouse)
            return

        warehouse = find_warehouse(connection)
        use(connection, UseResource.WAREHOUSE, warehouse)

    def connect(self) -> Connection:
        """enhance default behaviour to check role and warehouse"""
        connection = self.connection()
        self.role(connection)
        self.warehouse(connection)
        return connection
