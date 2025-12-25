from unittest.mock import patch

import pytest

from . import PowerbiClient, PowerbiCredentials
from .authentication import msal


@pytest.fixture
def mock_msal():
    with patch.object(msal, "ConfidentialClientApplication") as mock_app:
        mock_app.return_value.acquire_token_for_client.return_value = {
            "access_token": "fake_token"
        }
        yield mock_app


@pytest.fixture
def client(mock_msal):
    creds = PowerbiCredentials(tenant_id="", client_id="", secret="pwd")
    return PowerbiClient(creds)


def test_test_connection(client):
    with patch.object(
        client.power_bi_client._auth, "refresh_token"
    ) as mock_refresh:
        client.test_connection()
        mock_refresh.assert_called_once()
