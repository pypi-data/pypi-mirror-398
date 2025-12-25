import itertools
import logging

from google.api_core.exceptions import Forbidden  # type: ignore
from google.cloud.bigquery import Client as GoogleCloudClient  # type: ignore
from google.cloud.bigquery.dataset import Dataset  # type: ignore
from google.oauth2.service_account import Credentials  # type: ignore

from ...utils import SqlalchemyClient, retry
from .types import SetTwoString

logger = logging.getLogger(__name__)

BIGQUERY_URI = "bigquery://"

CREDENTIALS_INFO_KEY = "credentials_info"
PROJECT_ID_KEY = "project_id"

_RETRY_NUMBER = 1
_RETRY_BASE_MS = 60_000


class BigQueryClient(SqlalchemyClient):
    """Connect to BigQuery and run SQL queries"""

    def __init__(
        self,
        credentials: dict,
        db_allowed: set[str] | None = None,
        db_blocked: set[str] | None = None,
        dataset_blocked: set[str] | None = None,
    ):
        super().__init__(credentials)
        self._db_allowed = db_allowed
        self._db_blocked = db_blocked
        self._dataset_blocked = dataset_blocked
        self.credentials = self._credentials()
        self.client = self._client()
        self._projects: list[str] | None = None
        self._datasets: list[Dataset] | None = None

    @staticmethod
    def name() -> str:
        return "BigQuery"

    def _keep_project(self, project: str) -> bool:
        if self._db_allowed and project not in self._db_allowed:
            return False
        if self._db_blocked and project in self._db_blocked:
            return False
        return True

    def _keep_dataset(self, dataset: str) -> bool:
        if not self._dataset_blocked:
            return True

        return dataset not in self._dataset_blocked

    def _engine_options(self, credentials: dict) -> dict:
        return {
            CREDENTIALS_INFO_KEY: credentials,
        }

    def _build_uri(self, credentials: dict) -> str:
        return BIGQUERY_URI

    def _credentials(self) -> Credentials:
        assert CREDENTIALS_INFO_KEY in self._options, (
            "Missing BigQuery credentials in engine's options"
        )
        credentials = self._options[CREDENTIALS_INFO_KEY]
        return Credentials.from_service_account_info(credentials)

    def _client(self) -> GoogleCloudClient:
        return GoogleCloudClient(
            project=self._options[CREDENTIALS_INFO_KEY].get(PROJECT_ID_KEY),
            credentials=self.credentials,
        )

    def _list_datasets(self) -> list[Dataset]:
        """
        Returns datasets available for the given GCP client
        Cache the result in self._datasets to reduce number of API calls
        """
        if self._datasets is None:
            self._datasets = [
                dataset
                for project_id in self.get_projects()
                for dataset in self.client.list_datasets(project_id)
                if self._keep_dataset(dataset.dataset_id)
            ]
        return self._datasets

    @retry(
        (Forbidden,),
        max_retries=_RETRY_NUMBER,
        base_ms=_RETRY_BASE_MS,
        log_exc_info=True,
    )
    def get_projects(self) -> list[str]:
        """
        Returns distinct project_id available for the given GCP client
        Cache the result in self._projects to reduce number of API calls.

        Note: Calling list_projects from GoogleCloudClient causes some
        ```
        google.api_core.exceptions.Forbidden: 403 GET https://bigquery.googleapis.com/bigquery/v2/projects?prettyPrint=false
        Quota exceeded: Your user exceeded quota for concurrent project.lists requests.
        ````
        In that case, task should retry automatically.
        """
        if self._projects is None:
            self._projects = [
                p.project_id
                for p in self.client.list_projects(retry=None)  # type: ignore
                if self._keep_project(p.project_id)
            ]
        return self._projects

    def get_regions(self) -> SetTwoString:
        """
        Returns (project_id, region) available for the given GCP client
        - Loops trough projects -> datasets -> region
        - Returns distinct values
        Example:
            project_A
                -> dataset_1:US
            project_B
                -> empty
            project_C
                -> dataset_2:EU
                -> dataset_3:EU
        Will return:
            { (p_A, US), (p_C, EU) }
        """
        return {
            (ds.project, ds._properties["location"])
            for ds in self._list_datasets()
        }

    def get_extended_regions(self) -> SetTwoString:
        """
        Returns all combinations of (project_id, region) for the given client
        - Fetch all projects
        - Fetch all regions (cross projects)
        - Returns a combination of the two lists
        Example:
            project_A
                -> dataset_1:US
            project_B
                -> empty
            project_C
                -> dataset_2:EU
                -> dataset_3:EU
        Will return:
            { (p_A, EU), (p_A, US), (p_B, EU), (p_B, US), (p_C, EU), (p_C, US) }
        """
        projects = self.get_projects()
        regions = {ds._properties["location"] for ds in self._list_datasets()}
        combinations = itertools.product(projects, regions)
        return set(combinations)

    def get_datasets(self) -> SetTwoString:
        """
        Returns distinct (project_id, dataset_id) available for the given GCP client
        """
        return {(ds.project, ds.dataset_id) for ds in self._list_datasets()}
