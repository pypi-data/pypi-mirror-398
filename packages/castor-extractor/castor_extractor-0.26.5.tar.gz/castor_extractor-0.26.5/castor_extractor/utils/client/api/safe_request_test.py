import io
from http import HTTPStatus

import pytest
from requests import HTTPError, Response

from .safe_request import (
    RequestSafeMode,
    handle_response,
)


def mock_response(status_code: int):
    response = Response()
    response.status_code = status_code
    response.raw = io.BytesIO(b'[{"data": "working"}]')
    return response


def test_http_error_with_no_safe_mode():
    with pytest.raises(HTTPError):
        handle_response(mock_response(HTTPStatus.FORBIDDEN))


def test_http_error_with_no_status_code():
    safe_params = RequestSafeMode(2)  # Caught

    with pytest.raises(HTTPError):
        handle_response(mock_response(HTTPStatus.FORBIDDEN), safe_params)


def test_http_error_with_status_code():
    safe_params = RequestSafeMode(2, (HTTPStatus.FORBIDDEN,))  # Caught

    def call():
        return handle_response(mock_response(HTTPStatus.FORBIDDEN), safe_params)

    assert call() == {}
    assert call() == {}

    with pytest.raises(HTTPError):
        call()


def test_http_error_with_multiple_status_code():
    safe_params = RequestSafeMode(
        2, (HTTPStatus.NOT_FOUND, HTTPStatus.FORBIDDEN)
    )  # Caught

    def call():
        return handle_response(mock_response(HTTPStatus.FORBIDDEN), safe_params)

    def call_2():
        return handle_response(mock_response(HTTPStatus.NOT_FOUND), safe_params)

    assert call() == {}
    assert call_2() == {}
    with pytest.raises(HTTPError):  # 3 failed calls > retries
        call()


def test_http_error_with_wrong_status_code():
    safe_params = RequestSafeMode(2, (HTTPStatus.NOT_FOUND,))  # Wrong Status

    def call():
        handle_response(mock_response(HTTPStatus.BAD_REQUEST), safe_params)

    with pytest.raises(HTTPError):
        call()


def test_http_error_with_return():
    safe_params = RequestSafeMode(2, (HTTPStatus.NOT_FOUND,))  # Wrong Status

    def call():
        return handle_response(mock_response(HTTPStatus.OK), safe_params)

    assert call() == [{"data": "working"}]
