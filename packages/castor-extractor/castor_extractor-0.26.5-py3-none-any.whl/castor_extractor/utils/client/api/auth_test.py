from .auth import BasicAuth, BearerAuth, CustomAuth


class _MockRequest:
    def __init__(self):
        self.headers = {}


class _CustomAuth(CustomAuth):
    def _authentication_header(self) -> dict[str, str]:
        return {"custom-token": "token"}


class _BearAuth(BearerAuth):
    def fetch_token(self) -> str | None:
        return "token"


def test_BasicAuth():
    prepared_request = _MockRequest()
    auth = BasicAuth(username="simple", password="basic")
    auth.__call__(prepared_request)
    assert prepared_request.headers == {
        "Authorization": "Basic c2ltcGxlOmJhc2lj"
    }


def test_BearerAuth():
    prepared_request = _MockRequest()
    auth = _BearAuth()
    auth.__call__(prepared_request)
    assert prepared_request.headers == {"Authorization": "Bearer token"}

    auth._token = "expired_token"
    auth.__call__(prepared_request)
    assert prepared_request.headers == {"Authorization": "Bearer expired_token"}

    auth.refresh_token()
    auth.__call__(prepared_request)
    assert prepared_request.headers == {"Authorization": "Bearer token"}


def test_CustomAuth():
    prepared_request = _MockRequest()
    auth = _CustomAuth()
    auth.__call__(prepared_request)
    assert prepared_request.headers == {"custom-token": "token"}
