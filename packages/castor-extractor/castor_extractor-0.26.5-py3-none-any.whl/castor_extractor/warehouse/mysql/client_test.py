from unittest.mock import patch

import pytest

from .client import DEFAULT_PORT, MySQLClient, _check_required_keys


def test__check_required_keys():
    invalid_creds = {"user": "toto"}
    with pytest.raises(KeyError):
        _check_required_keys(invalid_creds)

    valid_creds = {"user": "toto", "password": "toto", "host": "localhost"}
    _check_required_keys(valid_creds)

    valid_creds_with_other_keys = {**valid_creds, "some": "other", "keys": 0}
    _check_required_keys(valid_creds_with_other_keys)


@patch.object(MySQLClient, "__init__")
def test_build_uri(mocked_client):
    credentials = {
        "user": "peanut",
        "password": "butter",
        "host": "jelly",
    }
    result = MySQLClient._build_uri(mocked_client, credentials)
    assert result == f"mysql+pymysql://peanut:butter@jelly:{DEFAULT_PORT}"

    port = 4567
    credentials_with_port = {**credentials, "port": port}
    result = MySQLClient._build_uri(mocked_client, credentials_with_port)
    assert result == f"mysql+pymysql://peanut:butter@jelly:{port}"
