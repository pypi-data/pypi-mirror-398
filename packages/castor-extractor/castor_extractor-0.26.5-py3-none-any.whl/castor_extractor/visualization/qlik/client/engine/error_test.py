import pytest

from .constants import ACCESS_DENIED_ERROR_CODE, APP_SIZE_EXCEEDED_ERROR_CODE
from .error import (
    AccessDeniedError,
    AppSizeExceededError,
    JsonRpcError,
    raise_for_error,
)


def _error(error_code: int) -> dict:
    return {
        "message": "Houston, we have a problem",
        "code": error_code,
    }


def test_raise_for_error():
    any_message = {"hello": "world"}

    # no error
    response = {"everything is": "OK"}
    raise_for_error(any_message, response)

    # error
    response = {"error": _error(12)}
    with pytest.raises(JsonRpcError):
        raise_for_error(any_message, response)

    # access denied error
    response = {"error": _error(ACCESS_DENIED_ERROR_CODE)}
    with pytest.raises(AccessDeniedError):
        raise_for_error(any_message, response)

    # source size exceeded error
    response = {"error": _error(APP_SIZE_EXCEEDED_ERROR_CODE)}
    with pytest.raises(AppSizeExceededError):
        raise_for_error(any_message, response)
