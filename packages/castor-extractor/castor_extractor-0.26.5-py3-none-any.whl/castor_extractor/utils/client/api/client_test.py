from unittest.mock import patch

from requests import PreparedRequest, Request, Session

from .auth import BasicAuth
from .client import APIClient


class MockSession:
    def __init__(self):
        self.request_data = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def request(self, **kwargs) -> PreparedRequest:
        kwargs.pop("timeout")
        request = Request(**kwargs)
        prepared_request = Session().prepare_request(request=request)
        return prepared_request


@patch("requests.sessions.Session", MockSession)
def test__get():
    auth = BasicAuth(username="user_id", password="secret")
    client = APIClient(
        auth=auth,
        host="https://example.api.com/v1/",
        headers={"content-type": "test"},
        timeout=9,
    )

    prepared_request = client._call("GET", "endpoint")

    # test method
    assert prepared_request.method == "GET"

    # test headers
    assert prepared_request.headers["content-type"] == "test"
    assert (
        prepared_request.headers["Authorization"]
        == "Basic dXNlcl9pZDpzZWNyZXQ="
    )
    assert prepared_request.url == "https://example.api.com/v1/endpoint"
