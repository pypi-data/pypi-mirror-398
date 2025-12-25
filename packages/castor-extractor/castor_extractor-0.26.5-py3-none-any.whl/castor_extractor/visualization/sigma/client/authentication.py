import logging
import threading
import time

import requests

from ....utils import (
    BearerAuth,
    build_url,
    handle_response,
)
from .endpoints import (
    SigmaEndpointFactory,
)

logger = logging.getLogger(__name__)


_AUTH_TIMEOUT_S = 60
_REFRESH_BUFFER_S = 300


class SigmaBearerAuth(BearerAuth):
    def __init__(self, host: str, token_payload: dict[str, str]):
        auth_endpoint = SigmaEndpointFactory.authentication()
        self.authentication_url = build_url(host, auth_endpoint)
        self.token_payload = token_payload
        self._token_expires_at: float | None = None
        self._token_lock = threading.Lock()

    def fetch_token(self) -> str:
        """Returns the token and sets its expiration time."""
        token_api_path = self.authentication_url
        token_response = requests.post(
            token_api_path, data=self.token_payload, timeout=_AUTH_TIMEOUT_S
        )
        response_data = handle_response(token_response)
        expires_in_seconds = int(response_data["expires_in"])
        self._token_expires_at = time.time() + expires_in_seconds
        return response_data["access_token"]

    def _is_token_expired_or_expiring_soon(self) -> bool:
        """
        Returns True if the token is expired or will expire soon (within buffer time)
        """
        if self._token_expires_at is None:
            return False

        return time.time() >= (self._token_expires_at - _REFRESH_BUFFER_S)

    def _needs_refresh(self, force_refresh: bool = False) -> bool:
        """Returns True if the token needs to be refreshed."""
        is_expired = self._is_token_expired_or_expiring_soon()
        return not self._token or force_refresh or is_expired

    def _fetch_token(self, force_refresh: bool = False) -> str | None:
        """Returns the API token, refreshing it if needed (thread-safe)."""
        if not self._needs_refresh(force_refresh):
            return f"Bearer {self._token}"

        with self._token_lock:
            if not self._needs_refresh(force_refresh):
                return f"Bearer {self._token}"

            logger.info("Refreshing authentication token...")
            self._token = self.fetch_token()
            return f"Bearer {self._token}"
