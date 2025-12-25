import logging
from functools import partial

from tqdm import tqdm  # type: ignore

from ...utils import fetch_all_pages
from ...utils.salesforce import SalesforceBaseClient, SalesforceCredentials
from .format import SalesforceFormatter
from .pagination import SalesforceSQLPagination, format_sobject_query
from .soql import (
    DESCRIPTION_QUERY_TPL,
    SOBJECT_FIELDS_QUERY_TPL,
)

logger = logging.getLogger(__name__)


class SalesforceClient(SalesforceBaseClient):
    """
    Salesforce API client to extract sobjects
    """

    def __init__(self, credentials: SalesforceCredentials):
        super().__init__(credentials)
        self.formatter = SalesforceFormatter()

    @staticmethod
    def name() -> str:
        return "Salesforce"

    def fetch_sobjects(self) -> list[dict]:
        """Fetch all sobjects"""
        logger.info("Extracting sobjects")
        query = format_sobject_query()
        request_ = partial(
            self._get, endpoint=self.query_endpoint, params={"q": query}
        )
        results = fetch_all_pages(request_, SalesforceSQLPagination)
        return list(results)

    def fetch_fields(self, sobject_name: str) -> list[dict]:
        """Fetches fields of a given sobject"""
        query = SOBJECT_FIELDS_QUERY_TPL.format(
            entity_definition_id=sobject_name
        )
        response = self._get(self.tooling_endpoint, params={"q": query})
        return response["records"]

    def fetch_description(self, table_name: str) -> str | None:
        """Retrieve description of a table"""
        query = DESCRIPTION_QUERY_TPL.format(table_name=table_name)
        response = self._get(self.tooling_endpoint, params={"q": query})
        if not response["records"]:
            return None
        return response["records"][0]["Description"]

    def add_table_descriptions(self, sobjects: list[dict]) -> list[dict]:
        """
        Add table descriptions.
        We use the tooling API which does not handle well the LIMIT in SOQL
        so we have to retrieve descriptions individually
        """
        described_sobjects = []
        for sobject in sobjects:
            description = self.fetch_description(sobject["QualifiedApiName"])
            described_sobjects.append({**sobject, "Description": description})
        return described_sobjects

    def tables(self) -> list[dict]:
        """
        Get Salesforce sobjects as tables
        """
        sobjects = self.fetch_sobjects()
        logger.info(f"Extracted {len(sobjects)} sobjects")
        described_sobjects = self.add_table_descriptions(sobjects)
        return list(self.formatter.tables(described_sobjects))

    def columns(
        self, sobject_names: list[tuple[str, str]], show_progress: bool = True
    ) -> list[dict]:
        """
        Get salesforce sobject fields as columns
        show_progress: optionally deactivate the tqdm progress bar
        """
        sobject_fields: dict[str, list[dict]] = dict()
        for api_name, table_name in tqdm(
            sobject_names, disable=not show_progress
        ):
            fields = self.fetch_fields(api_name)
            sobject_fields[table_name] = fields
        return list(self.formatter.columns(sobject_fields))
