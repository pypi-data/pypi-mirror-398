import logging
from abc import ABC, abstractmethod
from typing import Union

from requests.auth import AuthBase, HTTPBasicAuth

logger = logging.getLogger(__name__)


class BasicAuth(HTTPBasicAuth):
    """
    Authentication for API using basic auth method

    - Instantiate with username and password
    - pass the Auth class to the APIClient
    """

    def refresh_token(self):
        pass


class CustomAuth(AuthBase, ABC):
    """
    Authentication for API using custom auth method

    You need to:
     - implement the `_authentication_header()` method
     - pass the Auth class to the APIClient
    """

    def refresh_token(self):
        """Method to refresh the token if token expires"""
        pass

    @abstractmethod
    def _authentication_header(self) -> dict[str, str]:
        pass

    def __call__(self, r):
        r.headers = {**r.headers, **self._authentication_header()}
        return r


class BearerAuth:
    """
    Authentication for API using Bearer tokens

    You need to:
    - implement the `fetch_token()` method
    - pass the Auth class to the APIClient
    """

    _token: str | None = None
    authentication_key = "Authorization"

    @abstractmethod
    def fetch_token(self) -> str | None:
        """Method that should return the bearer token"""
        pass

    def refresh_token(self):
        """Method to refresh the token if token expires"""
        self._fetch_token(force_refresh=True)

    def _fetch_token(self, force_refresh: bool = False) -> str | None:
        if not self._token or force_refresh:
            logger.info("Refreshing authentication token...")
            self._token = self.fetch_token()
        return f"Bearer {self._token}"

    def __call__(self, r):
        r.headers[self.authentication_key] = self._fetch_token()
        return r


Auth = Union[BasicAuth, CustomAuth, BearerAuth]
