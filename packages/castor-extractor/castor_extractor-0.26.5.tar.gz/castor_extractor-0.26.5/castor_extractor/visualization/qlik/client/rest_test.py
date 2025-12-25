from unittest.mock import call, patch

from .engine import QlikCredentials
from .rest import RestApiClient


def _check_called_once(
    client: RestApiClient,
    first_page_url: str,
    return_value: dict | None,
):
    with patch.object(RestApiClient, "_call") as mock_call:
        mock_call.return_value = return_value
        data = client._pager(first_page_url)

        expected = [] if not return_value else return_value["data"]
        assert data == expected

        mock_call.assert_called_once_with(first_page_url)


def test_rest_api_client_pager():
    dummy_server_url = "https://clic.kom"
    dummy_api_key = "i-am-the-key-dont-let-others-know-about"
    credentials = QlikCredentials(
        base_url=dummy_server_url,
        api_key=dummy_api_key,
    )
    client = RestApiClient(credentials=credentials)

    first_page_url = "https://clic.kom/assets"

    # no response -> 1 call
    _check_called_once(client, first_page_url, return_value=None)

    # no next page -> 1 call
    return_value = {"data": [1], "links": {}}
    _check_called_once(client, first_page_url, return_value=return_value)

    # next page = current page -> 1 call
    return_value = {"data": [1], "links": {"next": {"href": first_page_url}}}
    _check_called_once(client, first_page_url, return_value=return_value)

    # next page -> 2 calls
    another_page_url = "https://clic.kom/assets?page2"
    return_value = {"data": [1], "links": {"next": {"href": another_page_url}}}

    with patch.object(RestApiClient, "_call") as mock_call:
        mock_call.return_value = return_value

        data = client._pager(first_page_url)
        assert data == [1, 1]

        calls = [call(first_page_url), call(another_page_url)]
        mock_call.assert_has_calls(calls)
