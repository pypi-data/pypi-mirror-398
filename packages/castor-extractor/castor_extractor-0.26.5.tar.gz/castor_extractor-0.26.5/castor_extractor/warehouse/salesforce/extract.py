import logging

from ...utils import AbstractStorage, LocalStorage, write_summary
from ...utils.salesforce import SalesforceCredentials
from ..abstract import (
    EXTERNAL_LINEAGE_ASSETS,
    SupportedAssets,
    WarehouseAsset,
    WarehouseAssetGroup,
    common_args,
)
from .client import SalesforceClient

logger = logging.getLogger(__name__)


Paths = dict[str, str]

SALESFORCE_CATALOG_ASSETS: tuple[WarehouseAsset, ...] = (
    WarehouseAsset.TABLE,
    WarehouseAsset.COLUMN,
)

SALESFORCE_ASSETS: SupportedAssets = {
    WarehouseAssetGroup.CATALOG: SALESFORCE_CATALOG_ASSETS,
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
}


class SalesforceExtractionProcessor:
    """Salesforce API-based extraction management - warehouse part"""

    def __init__(
        self,
        client: SalesforceClient,
        storage: AbstractStorage,
        skip_existing: bool = False,
    ):
        self._client = client
        self._storage = storage
        self._skip_existing = skip_existing

    def _should_extract(self) -> bool:
        """helper function to determine whether we need to extract"""
        if not self._skip_existing:
            return True

        for asset in SALESFORCE_CATALOG_ASSETS:
            if not self._storage.exists(asset.value):
                return True

        logger.info("Skipped, files for catalog already exist")
        return False

    def _existing_group_paths(self) -> Paths:
        return {
            a.value: self._storage.path(a.value)
            for a in SALESFORCE_CATALOG_ASSETS
        }

    def extract_catalog(self, show_progress: bool = True) -> Paths:
        """
        Extract the following catalog assets: tables and columns
        and return the locations of the extracted data
        """
        if not self._should_extract():
            return self._existing_group_paths()

        catalog_locations: Paths = dict()

        tables = self._client.tables()
        location = self._storage.put(WarehouseAsset.TABLE.value, tables)
        catalog_locations[WarehouseAsset.TABLE.value] = location
        logger.info(f"Extracted {len(tables)} tables to {location}")

        sobject_names = [(t["api_name"], t["table_name"]) for t in tables]
        columns = self._client.columns(sobject_names, show_progress)
        location = self._storage.put(WarehouseAsset.COLUMN.value, columns)
        catalog_locations[WarehouseAsset.COLUMN.value] = location
        logger.info(f"Extracted {len(columns)} columns to {location}")
        return catalog_locations

    def extract_role(self) -> Paths:
        """extract no users and return the empty file location"""
        users: list[dict] = []
        location = self._storage.put(WarehouseAsset.USER.value, users)
        logger.info(f"Extracted {len(users)} users to {location}")
        return {WarehouseAsset.USER.value: location}


def extract_all(**kwargs) -> None:
    """
    Extract all assets from Salesforce and store the results in CSV files
    """
    output_directory, skip_existing = common_args(kwargs)

    client = SalesforceClient(credentials=SalesforceCredentials(**kwargs))
    storage = LocalStorage(directory=output_directory)
    extractor = SalesforceExtractionProcessor(
        client=client,
        storage=storage,
        skip_existing=skip_existing,
    )

    extractor.extract_catalog()
    extractor.extract_role()

    write_summary(
        output_directory,
        storage.stored_at_ts,
        client_name=client.name(),
    )
