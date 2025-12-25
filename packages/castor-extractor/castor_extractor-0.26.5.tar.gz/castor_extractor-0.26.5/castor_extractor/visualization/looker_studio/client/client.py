from collections.abc import Iterator

from ....utils import empty_iterator
from ....warehouse.abstract import WarehouseAsset
from ....warehouse.bigquery import BigQueryClient, BigQueryQueryBuilder
from .. import LookerStudioAsset
from .admin_sdk_client import USER_EMAIL_FIELD, AdminSDKClient
from .credentials import LookerStudioCredentials
from .looker_studio_api_client import LookerStudioAPIClient

_ASSERT_ADMIN_SDK_CLIENT_MSG = "Missing Admin SDK client."
_ASSERT_BIGQUERY_CLIENT_MSG = "Missing BigQuery client."
_ASSERT_LOOKER_STUDIO_CLIENT_MSG = "Missing Looker Studio client."


class LookerStudioQueryBuilder(BigQueryQueryBuilder):
    def job_history_queries(self) -> list:
        """
        This class and method are a convenient workaround to build the
        ExtractionQueries which retrieve BigQuery's job history, but filtered on
        Looker Studio only.

        Compared to the generic BigQuery query history, only the SQL "template"
        changes. By defining this class here, this will pick the SQL file
        `queries/query.sql` located in the same directory as this file.
        """
        return super().build(WarehouseAsset.QUERY)  # type: ignore


class LookerStudioClient:
    """
    Acts as a wrapper class to fetch Looker Studio assets, which requires
    coordinating calls between
    - the Admin SDK API
    - the Looker Studio API
    - BigQuery (for source queries)

    All credentials are optional because the package command allows
    enabling/disabling specific extractions. For example, the user may not allow
    accessing Admin endpoints.

    See the following Notion page for more details about Domain-Wide Delegation
    and the different command line args:
    https://www.notion.so/castordoc/Looker-Studio-extract-source-queries-only-no-DWD-required-2aba1c3d458580d78199da6ca4c7f46f?source=copy_link
    """

    def __init__(
        self,
        credentials: LookerStudioCredentials | None = None,
        bigquery_credentials: dict | None = None,
        user_emails: list[str] | None = None,
        database_allowed: set[str] | None = None,
        database_blocked: set[str] | None = None,
    ):
        self.admin_sdk_client: AdminSDKClient | None = None
        self.bigquery_client: BigQueryClient | None = None
        self.looker_studio_client: LookerStudioAPIClient | None = None

        self.user_emails = user_emails

        self._initialize_clients(
            credentials=credentials,
            bigquery_credentials=bigquery_credentials,
            db_allowed=database_allowed,
            db_blocked=database_blocked,
        )

    def _initialize_clients(
        self,
        credentials: LookerStudioCredentials | None,
        bigquery_credentials: dict | None,
        db_allowed: set[str] | None,
        db_blocked: set[str] | None,
    ) -> None:
        if credentials:
            self.admin_sdk_client = AdminSDKClient(credentials)
            self.looker_studio_client = LookerStudioAPIClient(credentials)

        if bigquery_credentials:
            self.bigquery_client = BigQueryClient(
                credentials=bigquery_credentials,
                db_allowed=db_allowed,
                db_blocked=db_blocked,
            )

    def _list_user_emails(self) -> Iterator[str]:
        """
        Lists user emails either from a provided JSON file or via the Admin SDK API.

        Using all Google Workspace users can be inefficient for large clients -
        the client might spend hours checking thousands of users for Looker Studio
        assets when only a handful actually own any. A JSON file allows
        targeting known owners instead.
        """
        if self.user_emails is not None:
            yield from self.user_emails
            return

        assert self.admin_sdk_client, _ASSERT_ADMIN_SDK_CLIENT_MSG
        for user in self.admin_sdk_client.list_users():
            yield user[USER_EMAIL_FIELD]

    def _get_assets(self) -> Iterator[dict]:
        """
        Extracts reports and data sources user by user. The loop is necessary
        because the Looker Studio API can only retrieve the assets owned by a
        single user.
        """
        assert self.looker_studio_client, _ASSERT_LOOKER_STUDIO_CLIENT_MSG

        for user_email in self._list_user_emails():
            yield from self.looker_studio_client.fetch_user_assets(user_email)

    def _get_source_queries(self) -> Iterator[dict]:
        """
        Extracts the BigQuery jobs triggered by Looker Studio. The last job
        per data source is returned.
        """
        if not self.bigquery_client:
            return empty_iterator()

        query_builder = LookerStudioQueryBuilder(
            regions=self.bigquery_client.get_regions(),
            datasets=self.bigquery_client.get_datasets(),
            extended_regions=self.bigquery_client.get_extended_regions(),
        )

        queries = query_builder.job_history_queries()

        for query in queries:
            yield from self.bigquery_client.execute(query)

    def fetch(self, asset: LookerStudioAsset) -> Iterator[dict]:
        if asset == LookerStudioAsset.ASSETS:
            yield from self._get_assets()

        elif asset == LookerStudioAsset.SOURCE_QUERIES:
            yield from self._get_source_queries()

        elif asset == LookerStudioAsset.VIEW_ACTIVITY:
            assert self.admin_sdk_client, _ASSERT_ADMIN_SDK_CLIENT_MSG
            yield from self.admin_sdk_client.list_view_events()

        else:
            raise ValueError(f"The asset {asset}, is not supported")
