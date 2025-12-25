"""https://www.notion.so/castordoc/Workshop-Mocking-405ef02712e6446193720abf8d4c2f53"""

from unittest.mock import patch

from ...utils import SqlalchemyClient
from .client import SnowflakeClient, _scalar


class MockedResult:
    def scalar(self):
        return "foo"


class MockedConnection:
    def execute(self, query):
        return MockedResult()


def test_scalar():
    mocked_connection = MockedConnection()
    result = _scalar(mocked_connection, "SELECT foo FROM BAR;")
    assert result == "foo"


def get_snowflake_connection():
    credentials = {
        "account": "value_account",
        "user": "value_user",
        "password": "value_password",
    }
    return SnowflakeClient(credentials)


@patch.object(SqlalchemyClient, "__init__")
def test_build_uri(_):
    credentials = {
        "account": "value_account",
        "user": "value_user",
        "password": "value_password",
    }
    client = get_snowflake_connection()
    result = client._build_uri(credentials)
    assert (
        result
        == "snowflake://value_user:value_password@value_account/?application=castor"
    )


@patch.object(SqlalchemyClient, "__init__")
@patch(
    "source.packages.extractor.castor_extractor.warehouse.snowflake.client.use",
)
def test_role(mocked_used, _):
    client = get_snowflake_connection()
    client._role = "ACCOUNTADMIN"
    client.role(MockedConnection())
    mocked_used.assert_called_once()
