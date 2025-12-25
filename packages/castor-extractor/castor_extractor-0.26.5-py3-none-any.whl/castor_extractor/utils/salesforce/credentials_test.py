from .credentials import SalesforceCredentials


def test_Credentials_token_request_payload():
    creds = SalesforceCredentials(
        username="giphy",
        password="1312",
        client_id="degenie",
        client_secret="fautpasledire",
        security_token="yo",
        base_url="man",
    )

    payload = creds.token_request_payload()

    assert payload["grant_type"] == "password"
    assert payload["username"] == "giphy"
    assert payload["client_id"] == "degenie"
    assert payload["client_secret"] == "fautpasledire"
    assert payload["password"] == "1312yo"
