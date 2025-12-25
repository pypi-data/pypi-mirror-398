import logging
from collections.abc import Callable
from http import HTTPStatus
from typing import Literal, Optional

import requests
from requests import Response

from ...retry import retry, retry_request
from .auth import Auth
from .safe_request import RequestSafeMode, handle_response
from .utils import build_url

logger = logging.getLogger(__name__)

Headers = Optional[dict[str, str]]

# https://requests.readthedocs.io/en/latest/api/#requests.request
HttpMethod = Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"]

DEFAULT_TIMEOUT = 60
RETRY_ON_EXPIRED_TOKEN = 1
RETRY_ON_GATEWAY_TIMEOUT = 3

_TIMEOUT_RETRY_BASE_MS = 10 * 60 * 1000  # 10 minutes
_TIMEOUT_RETRY_COUNT = 2
_TIMEOUT_RETRY_EXCEPTIONS = (requests.exceptions.Timeout,)


def _generate_payloads(
    method: HttpMethod,
    params: dict | None,
    data: dict | None,
    pagination_params: dict | None,
) -> tuple[dict | None, dict | None]:
    _pagination_params = pagination_params or {}

    if method == "GET":
        params = params or {}
        params = {**params, **_pagination_params}
        return data, params
    if method == "POST":
        data = data or {}
        data = {**data, **_pagination_params}
        return data, params
    raise ValueError(f"Method {method} is not yet supported")


class APIClient:
    """
    Interface to easily query REST-API with GET and POST requests

    Args:
        auth: auth class to enable logging to the API
        host: base url of the API
        headers: common headers to all calls that will be made
        timeout: read timeout for each request
        safe_mode: ignore certain exceptions based on status codes

    Note:
        If the auth implements a refreshing mechanism (refresh_token)
        the token is automatically refreshed once upon receiving the
        401: UNAUTHORIZED status code
    """

    def __init__(
        self,
        auth: Auth,
        host: str | None = None,
        headers: Headers = None,
        timeout: int = DEFAULT_TIMEOUT,
        safe_mode: RequestSafeMode = RequestSafeMode(),
    ):
        self.base_headers = headers or {}
        self._host = host
        self._timeout = timeout
        self._auth = auth
        self._safe_mode = safe_mode

    def _call(
        self,
        method: HttpMethod,
        endpoint: str,
        *,
        headers: Headers = None,
        params: dict | None = None,
        data: dict | None = None,
        pagination_params: dict | None = None,
        retry_on_timeout: bool = True,
    ) -> Response:
        headers = headers or {}

        data, params = _generate_payloads(
            method=method,
            params=params,
            data=data,
            pagination_params=pagination_params,
        )

        url = build_url(self._host, endpoint)

        if retry_on_timeout:
            retry_wrapper = retry(
                exceptions=_TIMEOUT_RETRY_EXCEPTIONS,
                max_retries=_TIMEOUT_RETRY_COUNT,
                base_ms=_TIMEOUT_RETRY_BASE_MS,
            )
            request_fn = retry_wrapper(requests.request)
        else:
            request_fn = requests.request

        return request_fn(
            method=method,
            url=url,
            auth=self._auth,
            headers={**self.base_headers, **headers},
            params=params,
            json=data,
            timeout=self._timeout,
        )

    @retry_request(
        status_codes=(HTTPStatus.GATEWAY_TIMEOUT,),
        max_retries=RETRY_ON_GATEWAY_TIMEOUT,
    )
    @retry_request(
        status_codes=(HTTPStatus.UNAUTHORIZED,),
        max_retries=RETRY_ON_EXPIRED_TOKEN,
    )
    def _get(
        self,
        endpoint: str,
        *,
        headers: Headers = None,
        params: dict | None = None,
        data: dict | None = None,
        pagination_params: dict | None = None,
        retry_on_timeout: bool = True,
    ):
        response = self._call(
            method="GET",
            endpoint=endpoint,
            params=params,
            data=data,
            pagination_params=pagination_params,
            headers=headers,
            retry_on_timeout=retry_on_timeout,
        )
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            self._auth.refresh_token()

        return handle_response(response, safe_mode=self._safe_mode)

    @retry_request(
        status_codes=(HTTPStatus.UNAUTHORIZED,),
        max_retries=RETRY_ON_EXPIRED_TOKEN,
    )
    def _post(
        self,
        endpoint: str,
        *,
        headers: Headers = None,
        params: dict | None = None,
        data: dict | None = None,
        pagination_params: dict | None = None,
        handler: Callable | None = None,
    ):
        response = self._call(
            method="POST",
            endpoint=endpoint,
            params=params,
            data=data,
            pagination_params=pagination_params,
            headers=headers,
        )
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            self._auth.refresh_token()

        return handle_response(
            response, safe_mode=self._safe_mode, handler=handler
        )
