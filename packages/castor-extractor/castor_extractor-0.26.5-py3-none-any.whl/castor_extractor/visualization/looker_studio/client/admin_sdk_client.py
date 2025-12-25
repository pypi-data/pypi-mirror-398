from collections.abc import Iterator

from google.oauth2.service_account import Credentials
from googleapiclient import discovery  # type: ignore

from ....utils import (
    at_midnight,
    current_date,
    fetch_all_pages,
    format_rfc_3339_date,
    past_date,
)
from .credentials import LookerStudioCredentials
from .pagination import LookerStudioPagination

USER_EMAIL_FIELD = "primaryEmail"


class AdminSDKClient:
    """
    Client to call the Report API and Directory API.
    The service account must impersonate and admin account.
    """

    def __init__(self, credentials: LookerStudioCredentials):
        self._credentials = Credentials.from_service_account_info(
            credentials.model_dump(),
            scopes=credentials.scopes,
            subject=credentials.admin_email,  # impersonates an admin
        )
        self.directory_api = discovery.build(
            "admin", "directory_v1", credentials=self._credentials
        )
        self.report_api = discovery.build(
            "admin", "reports_v1", credentials=self._credentials
        )

    def list_users(self) -> Iterator[dict]:
        """
        Lists all users in the domain; only the primaryEmail field is selected.
        Note:
        * `my_customer` is an alias to represent the account's `customerId`
        * `domain_public` allows non-admins to list users. This is technically
           not necessary here because an admin account is impersonated, but it
           avoids tapping into unnecessary data & serves for future reference.
        See
            https://googleapis.github.io/google-api-python-client/docs/dyn/admin_directory_v1.users.html#list
            https://developers.google.com/admin-sdk/directory/reference/rest/v1/users/list
            https://developers.google.com/admin-sdk/directory/v1/guides/manage-users#retrieve_users_non_admin
            https://stackoverflow.com/a/71083443/14448410
        """

        def _users(pagination_params: dict | None = None) -> dict:
            parameters = {
                "viewType": "domain_public",
                "customer": "my_customer",
                "fields": f"users({USER_EMAIL_FIELD}), nextPageToken",
                **(pagination_params or {}),
            }

            return self.directory_api.users().list(**parameters).execute()

        yield from fetch_all_pages(_users, LookerStudioPagination)

    def list_view_events(self) -> Iterator[dict]:
        """
        Lists all Data Studio View events of the past day.
        See
            https://googleapis.github.io/google-api-python-client/docs/dyn/admin_reports_v1.activities.html
            https://developers.google.com/admin-sdk/reports/reference/rest/v1/activities/list
            https://developers.google.com/admin-sdk/reports/v1/appendix/activity/data-studio#VIEW
        """

        def _activity(pagination_params: dict | None = None) -> dict:
            yesterday = format_rfc_3339_date(at_midnight(past_date(1)))
            today = format_rfc_3339_date(at_midnight(current_date()))

            parameters = {
                "userKey": "all",
                "applicationName": "data_studio",
                "eventName": "VIEW",
                "startTime": yesterday,
                "endTime": today,
                **(pagination_params or {}),
            }

            return self.report_api.activities().list(**parameters).execute()

        yield from fetch_all_pages(_activity, LookerStudioPagination)
