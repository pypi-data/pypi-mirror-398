from unittest.mock import Mock, patch

import pytest
from requests import HTTPError

from .authentication import msal
from .credentials import PowerbiCredentials
from .graph_api_client import (
    MicrosoftGraphAccessForbidden,
    MicrosoftGraphPIClient,
)


@pytest.fixture
def mock_msal():
    with patch.object(msal, "ConfidentialClientApplication") as mock_app:
        mock_app.return_value.acquire_token_for_client.return_value = {
            "access_token": "fake_token"
        }
        yield mock_app


@pytest.fixture
def graph_client(mock_msal):
    creds = PowerbiCredentials(
        tenant_id="tenant", client_id="client", secret="pwd"
    )
    return MicrosoftGraphPIClient(creds)


def test__users_in_groups(graph_client):
    mock_response = Mock(status_code=403)
    http_error = HTTPError()
    http_error.response = mock_response

    with patch.object(graph_client, "_get", side_effect=http_error):
        with pytest.raises(MicrosoftGraphAccessForbidden):
            list(graph_client.users_in_groups(["id"]))
