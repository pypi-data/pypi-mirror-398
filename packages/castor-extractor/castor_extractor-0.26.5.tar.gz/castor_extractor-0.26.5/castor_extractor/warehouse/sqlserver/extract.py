import logging

from ...utils import LocalStorage, filter_items, from_env, write_summary
from ..abstract import (
    CATALOG_ASSETS,
    EXTERNAL_LINEAGE_ASSETS,
    QUERIES_ASSETS,
    VIEWS_ASSETS,
    SQLExtractionProcessor,
    SupportedAssets,
    WarehouseAsset,
    WarehouseAssetGroup,
    common_args,
    extractable_asset_groups,
)
from .client import MSSQLClient
from .query import MSSQLQueryBuilder

logger = logging.getLogger(__name__)


MSSQL_ASSETS: SupportedAssets = {
    WarehouseAssetGroup.CATALOG: CATALOG_ASSETS,
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
    WarehouseAssetGroup.QUERY: QUERIES_ASSETS,
    WarehouseAssetGroup.ROLE: (WarehouseAsset.USER,),
    WarehouseAssetGroup.VIEW_DDL: VIEWS_ASSETS,
}


MSSQL_USER = "CASTOR_MSSQL_USER"
MSSQL_PASSWORD = "CASTOR_MSSQL_PASSWORD"  # noqa: S105
MSSQL_HOST = "CASTOR_MSSQL_HOST"
MSSQL_PORT = "CASTOR_MSSQL_PORT"


def _credentials(params: dict) -> dict:
    """extract mssql credentials"""

    return {
        "user": params.get("user") or from_env(MSSQL_USER),
        "password": params.get("password") or from_env(MSSQL_PASSWORD),
        "host": params.get("host") or from_env(MSSQL_HOST),
        "port": params.get("port") or from_env(MSSQL_PORT),
    }


def extract_all(**kwargs) -> None:
    """
    Extract all assets from mssql and store the results in CSV files
    """
    output_directory, skip_existing = common_args(kwargs)

    client = MSSQLClient(credentials=_credentials(kwargs))

    databases = filter_items(
        items=client.get_databases(),
        allowed=kwargs.get("db_allowed"),
        blocked=kwargs.get("db_blocked"),
    )

    logger.info(f"Available databases: {databases}\n")

    query_builder = MSSQLQueryBuilder(
        databases=databases,
    )

    storage = LocalStorage(directory=output_directory)

    extractor = SQLExtractionProcessor(
        client=client,
        query_builder=query_builder,
        storage=storage,
    )

    skip_queries = kwargs.get("skip_queries") or False
    for group in extractable_asset_groups(MSSQL_ASSETS):
        if group == WarehouseAssetGroup.QUERY and skip_queries:
            continue
        for asset in group:
            logger.info(f"Extracting `{asset.value.upper()}` ...")
            location = extractor.extract(asset, skip_existing)
            logger.info(f"Results stored to {location}\n")

    write_summary(
        output_directory,
        storage.stored_at_ts,
        client_name=client.name(),
    )
