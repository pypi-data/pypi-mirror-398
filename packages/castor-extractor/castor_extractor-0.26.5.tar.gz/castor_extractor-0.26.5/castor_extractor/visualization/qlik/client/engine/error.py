from .constants import (
    ACCESS_DENIED_ERROR_CODE,
    APP_SIZE_EXCEEDED_ERROR_CODE,
    PERSISTENCE_READ_FAILED_ERROR_CODE,
)


class JsonRpcError(Exception):
    """
    Error class to be raised when a JSON-RPC call response is an error
    """

    def __init__(self, message: dict, error: dict):
        self.message = message
        self.error = error

        name = self.__class__.__name__
        super().__init__({"type": name, "message": message, "error": error})


class AccessDeniedError(JsonRpcError):
    """
    Error class to be raised when JSON-RPC error is access denied
    """

    ...


class AppSizeExceededError(JsonRpcError):
    """
    Error class to be raised when JSON-RPC error is source size exceeded
    """

    ...


class PersistenceReadFailedError(JsonRpcError):
    """
    Error class to be raised when JSON-RPC error is persistence read failed
    """


class QlikResponseKeyError(Exception):
    """
    Error class to be raised when an expected Key is missing from the JSON-RPC response
    """


ERROR_CODE_MAPPING: dict[int, type[JsonRpcError]] = {
    ACCESS_DENIED_ERROR_CODE: AccessDeniedError,
    APP_SIZE_EXCEEDED_ERROR_CODE: AppSizeExceededError,
    PERSISTENCE_READ_FAILED_ERROR_CODE: PersistenceReadFailedError,
}


def raise_for_error(message: dict, response: dict) -> None:
    """Raises JsonRpcError when response is an error"""
    error = response.get("error")
    if not error:
        return None

    error_code = error["code"]
    exception = ERROR_CODE_MAPPING.get(error_code, JsonRpcError)
    raise exception(message, response["error"])
