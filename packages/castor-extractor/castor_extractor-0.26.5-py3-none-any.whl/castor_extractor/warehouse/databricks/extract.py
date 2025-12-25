import logging
from datetime import date
from typing import Optional

from ...exceptions import (
    NoDatabaseProvidedException,
)
from ...utils import AbstractStorage, LocalStorage, write_summary
from ..abstract import (
    ADDITIONAL_LINEAGE_ASSETS,
    CATALOG_ASSETS,
    EXTERNAL_LINEAGE_ASSETS,
    QUERIES_ASSETS,
    VIEWS_ASSETS,
    SupportedAssets,
    TimeFilter,
    WarehouseAsset,
    WarehouseAssetGroup,
    common_args,
)
from .client import DatabricksClient
from .credentials import DatabricksCredentials
from .enums import LineageEntity

DATABRICKS_ASSETS: SupportedAssets = {
    WarehouseAssetGroup.ADDITIONAL_LINEAGE: ADDITIONAL_LINEAGE_ASSETS,
    WarehouseAssetGroup.CATALOG: CATALOG_ASSETS,
    WarehouseAssetGroup.QUERY: QUERIES_ASSETS,
    WarehouseAssetGroup.ROLE: (WarehouseAsset.USER,),
    WarehouseAssetGroup.VIEW_DDL: VIEWS_ASSETS,
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
}

logger = logging.getLogger(__name__)

OTimeFilter = Optional[TimeFilter]
Paths = dict[str, str]


def _day(time_filter: OTimeFilter) -> date:
    if not time_filter:
        return TimeFilter.default().day
    return time_filter.day


class DatabricksExtractionProcessor:
    """Databricks' API-based extraction management"""

    def __init__(
        self,
        client: DatabricksClient,
        storage: AbstractStorage,
        skip_existing: bool = False,
    ):
        self._client = client
        self._storage = storage
        self._skip_existing = skip_existing

    def _should_not_reextract(self, asset_group: WarehouseAssetGroup) -> bool:
        """helper function to determine whether we need to extract"""
        if not self._skip_existing:
            return False

        for asset in DATABRICKS_ASSETS[asset_group]:
            if not self._storage.exists(asset.value):
                return False

        logger.info(f"Skipped, files for {asset_group.value} already exist")
        return True

    def _existing_group_paths(self, asset_group: WarehouseAssetGroup) -> Paths:
        return {
            a.value: self._storage.path(a.value)
            for a in DATABRICKS_ASSETS[asset_group]
        }

    def extract_catalog(self) -> Paths:
        """
        Extract all catalog assets (from database to column)
        and return the locations of the extracted data
        """
        if self._should_not_reextract(WarehouseAssetGroup.CATALOG):
            return self._existing_group_paths(WarehouseAssetGroup.CATALOG)

        catalog_locations: dict[str, str] = dict()
        databases = self._client.databases()
        location = self._storage.put(WarehouseAsset.DATABASE.value, databases)
        catalog_locations[WarehouseAsset.DATABASE.value] = location
        logger.info(f"Extracted {len(databases)} databases to {location}")

        schemas = self._client.schemas(databases)
        location = self._storage.put(WarehouseAsset.SCHEMA.value, schemas)
        catalog_locations[WarehouseAsset.SCHEMA.value] = location
        logger.info(f"Extracted {len(schemas)} schemas to {location}")

        del databases

        users = self._client.users()
        tables, columns = self._client.tables_and_columns(schemas, users)

        location = self._storage.put(WarehouseAsset.TABLE.value, tables)
        catalog_locations[WarehouseAsset.TABLE.value] = location
        logger.info(f"Extracted {len(tables)} tables to {location}")

        location = self._storage.put(WarehouseAsset.COLUMN.value, columns)
        catalog_locations[WarehouseAsset.COLUMN.value] = location
        logger.info(f"Extracted {len(columns)} columns to {location}")
        return catalog_locations

    def extract_lineage(self, time_filter: OTimeFilter = None) -> Paths:
        if self._should_not_reextract(WarehouseAssetGroup.ADDITIONAL_LINEAGE):
            return self._existing_group_paths(
                WarehouseAssetGroup.ADDITIONAL_LINEAGE
            )
        lineage_locations: dict[str, str] = dict()

        day = _day(time_filter)
        client = self._client.sql_client

        # extract table lineage
        table_lineage = client.get_lineage(LineageEntity.TABLE, day)
        table_lineage_key = WarehouseAsset.ADDITIONAL_TABLE_LINEAGE.value
        location = self._storage.put(table_lineage_key, table_lineage)
        lineage_locations[table_lineage_key] = location
        msg = f"Extracted {len(table_lineage)} table lineage to {location}"
        logger.info(msg)

        # extract column lineage
        column_lineage = client.get_lineage(LineageEntity.COLUMN, day)
        column_lineage_key = WarehouseAsset.ADDITIONAL_COLUMN_LINEAGE.value
        location = self._storage.put(column_lineage_key, column_lineage)
        lineage_locations[column_lineage_key] = location
        msg = f"Extracted {len(column_lineage)} column lineage to {location}"
        logger.info(msg)
        return lineage_locations

    def extract_query(self, time_filter: OTimeFilter = None) -> Paths:
        """extract yesterday's queries and return their location"""
        if self._should_not_reextract(WarehouseAssetGroup.QUERY):
            return self._existing_group_paths(WarehouseAssetGroup.QUERY)

        queries = self._client.queries(time_filter)
        location = self._storage.put(WarehouseAsset.QUERY.value, queries)
        logger.info(f"Extracted {len(queries)} queries to {location}")
        return {WarehouseAsset.QUERY.value: location}

    def extract_role(self) -> Paths:
        """extract roles (users) and return their location"""
        if self._should_not_reextract(WarehouseAssetGroup.ROLE):
            return self._existing_group_paths(WarehouseAssetGroup.ROLE)

        users = self._client.users()
        location = self._storage.put(WarehouseAsset.USER.value, users)
        logger.info(f"Extracted {len(users)} users to {location}")
        return {WarehouseAsset.USER.value: location}

    def extract_view_ddl(self) -> Paths:
        """extract view ddl (using the same route as tables)"""
        if self._should_not_reextract(WarehouseAssetGroup.VIEW_DDL):
            return self._existing_group_paths(WarehouseAssetGroup.VIEW_DDL)

        databases = self._client.databases()
        schemas = self._client.schemas(databases)
        view_ddl = self._client.view_ddl(schemas)
        location = self._storage.put(WarehouseAsset.VIEW_DDL.value, view_ddl)
        logger.info(f"Extracted {len(view_ddl)} view_ddl to {location}")
        return {WarehouseAsset.VIEW_DDL.value: location}


def extract_all(**kwargs) -> None:
    """
    Extract all assets from Databricks and store the results in CSV files
    Time filter scope for `Queries` = the day before (from 12AM to 12AM)
    """
    output_directory, skip_existing = common_args(kwargs)

    client = DatabricksClient(
        credentials=DatabricksCredentials(**kwargs),
        db_allowed=kwargs.get("db_allowed"),
        db_blocked=kwargs.get("db_blocked"),
    )

    if not client.databases():
        raise NoDatabaseProvidedException

    storage = LocalStorage(directory=output_directory)

    extractor = DatabricksExtractionProcessor(
        client=client,
        storage=storage,
        skip_existing=skip_existing,
    )

    extractor.extract_catalog()
    extractor.extract_lineage()
    extractor.extract_query()
    extractor.extract_role()
    extractor.extract_view_ddl()

    write_summary(
        output_directory,
        storage.stored_at_ts,
        client_name=client.name(),
    )
