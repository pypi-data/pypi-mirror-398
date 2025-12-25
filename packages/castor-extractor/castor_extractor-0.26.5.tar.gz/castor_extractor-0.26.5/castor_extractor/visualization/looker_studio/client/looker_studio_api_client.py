from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from http import HTTPStatus

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

from ....utils import (
    APIClient,
    BearerAuth,
    RequestSafeMode,
    fetch_all_pages,
)
from .credentials import LookerStudioCredentials
from .endpoints import LookerStudioAPIEndpoint
from .enums import LookerStudioAssetType
from .pagination import LookerStudioPagination


@contextmanager
def temporary_safe_request(client: APIClient):
    """
    Allows applying the safe mode only to specific requests instead of all
    API calls.
    """
    client._safe_mode = RequestSafeMode(
        max_errors=float("inf"),
        status_codes=(HTTPStatus.UNAUTHORIZED,),
    )
    try:
        yield client
    finally:
        client._safe_mode = RequestSafeMode()


class LookerStudioAPIAuth(BearerAuth):
    def __init__(
        self,
        credentials: LookerStudioCredentials,
        subject: str | None = None,
    ):
        """
        Instantiates the service account credentials.
        If a `subject` email is passed, the service account will impersonate
        that user and make requests on that user's behalf.
        """
        self._credentials = Credentials.from_service_account_info(
            credentials.model_dump(),
            scopes=credentials.scopes,
        )
        if subject:
            self._credentials = self._credentials.with_subject(subject)

    def fetch_token(self):
        self._credentials.refresh(Request())
        return self._credentials.token


class LookerStudioAPIClient(APIClient):
    def __init__(self, credentials: LookerStudioCredentials):
        auth = LookerStudioAPIAuth(credentials=credentials)
        super().__init__(auth=auth)

        self._credentials = credentials

    def _is_private_asset(self, asset_name: str) -> bool:
        """
        Returns True if the asset is not viewable by anyone other than the owner.

        The permissions	dict contains `Role: Member[]` key-value pairs and has
        at least one key-value pair to define the asset's unique OWNER.
        If another key is present, it means the asset was shared with
        another person or group.

        See also https://developers.google.com/looker-studio/integrate/api/reference/types#Permissions
        """
        with temporary_safe_request(self):
            data = self._get(LookerStudioAPIEndpoint.permissions(asset_name))
            permissions = data.get("permissions")

            if not permissions:
                return True

            return len(permissions.keys()) == 1

    def _user_assets(
        self, asset_type: LookerStudioAssetType, user_email: str
    ) -> Iterator[dict]:
        """
        Yields all assets of the given type, owned by the given user and visible
        by other members.
        """
        request = partial(
            self._get,
            LookerStudioAPIEndpoint.search(),
            params={"assetTypes": [asset_type.value]},
        )
        assets = fetch_all_pages(request, LookerStudioPagination)

        for asset in assets:
            asset_name = asset["name"]
            owner = asset.get("owner", "")
            if owner == user_email and not self._is_private_asset(asset_name):
                yield asset

    def _impersonate_user(self, user_email: str):
        self._auth = LookerStudioAPIAuth(
            credentials=self._credentials, subject=user_email
        )

    def fetch_user_assets(self, user_email: str) -> Iterator[dict]:
        """Yields assets (reports and data sources) shared by the given user."""
        self._impersonate_user(user_email)

        reports = self._user_assets(
            asset_type=LookerStudioAssetType.REPORT,
            user_email=user_email,
        )
        data_sources = self._user_assets(
            asset_type=LookerStudioAssetType.DATA_SOURCE,
            user_email=user_email,
        )

        yield from reports
        yield from data_sources
