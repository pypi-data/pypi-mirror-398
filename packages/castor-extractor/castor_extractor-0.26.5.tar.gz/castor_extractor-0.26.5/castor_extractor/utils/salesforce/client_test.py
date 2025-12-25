from unittest.mock import patch

from .client import SalesforceBaseClient
from .credentials import SalesforceCredentials


@patch.object(SalesforceBaseClient, "_call")
def test_SalesforceBaseClient__urls(mock_call):
    mock_call.return_value = {"access_token": "the_token"}
    credentials = SalesforceCredentials(
        username="usr",
        password="pw",
        client_id="key",
        client_secret="secret",
        security_token="token",
        base_url="url",
    )
    client = SalesforceBaseClient(credentials)

    assert client.query_endpoint == "services/data/v59.0/query"
    assert client.tooling_endpoint == "services/data/v59.0/tooling/query"
