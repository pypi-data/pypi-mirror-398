import logging

from ...utils import LocalStorage, from_env, write_summary
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
from .client import MySQLClient
from .query import MySQLQueryBuilder

logger = logging.getLogger(__name__)


MYSQL_ASSETS: SupportedAssets = {
    WarehouseAssetGroup.CATALOG: CATALOG_ASSETS,
    WarehouseAssetGroup.QUERY: QUERIES_ASSETS,
    WarehouseAssetGroup.VIEW_DDL: VIEWS_ASSETS,
    WarehouseAssetGroup.ROLE: (WarehouseAsset.USER,),
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
}

MYSQL_USER = "CASTOR_MYSQL_USER"
MYSQL_PASSWORD = "CASTOR_MYSQL_PASSWORD"  # noqa: S105
MYSQL_HOST = "CASTOR_MYSQL_HOST"
MYSQL_PORT = "CASTOR_MYSQL_PORT"


def _credentials(params: dict) -> dict:
    """Extract MySQL credentials"""

    return {
        "user": params.get("user") or from_env(MYSQL_USER),
        "password": params.get("password") or from_env(MYSQL_PASSWORD),
        "host": params.get("host") or from_env(MYSQL_HOST),
        "port": params.get("port") or from_env(MYSQL_PORT, allow_missing=True),
    }


def extract_all(**kwargs) -> None:
    """
    Extract all assets from MySQL and store the results in CSV files
    """
    output_directory, skip_existing = common_args(kwargs)

    client = MySQLClient(credentials=_credentials(kwargs))
    query_builder = MySQLQueryBuilder()

    storage = LocalStorage(directory=output_directory)
    extractor = SQLExtractionProcessor(
        client=client,
        query_builder=query_builder,
        storage=storage,
    )

    for group in extractable_asset_groups(MYSQL_ASSETS):
        for asset in group:
            logger.info(f"Extracting `{asset.value.upper()}` ...")
            location = extractor.extract(asset, skip_existing)
            logger.info(f"Results stored to {location}\n")

    write_summary(
        output_directory,
        storage.stored_at_ts,
        client_name=client.name(),
    )
