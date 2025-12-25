import logging

from ...utils import LocalStorage, PostgresClient, from_env, write_summary
from ..abstract import (
    CATALOG_ASSETS,
    EXTERNAL_LINEAGE_ASSETS,
    SQLExtractionProcessor,
    SupportedAssets,
    WarehouseAsset,
    WarehouseAssetGroup,
    common_args,
    extractable_asset_groups,
)
from .query import PostgresQueryBuilder

logger = logging.getLogger(__name__)


POSTGRES_ASSETS: SupportedAssets = {
    WarehouseAssetGroup.CATALOG: CATALOG_ASSETS,
    WarehouseAssetGroup.ROLE: (
        WarehouseAsset.GROUP,
        WarehouseAsset.USER,
    ),
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
}


POSTGRES_USER = "CASTOR_POSTGRES_USER"
POSTGRES_PASSWORD = "CASTOR_POSTGRES_PASSWORD"  # noqa: S105
POSTGRES_HOST = "CASTOR_POSTGRES_HOST"
POSTGRES_PORT = "CASTOR_POSTGRES_PORT"
POSTGRES_DATABASE = "CASTOR_POSTGRES_DATABASE"


def _credentials(params: dict) -> dict:
    """extract Postgres credentials"""

    return {
        "user": params.get("user") or from_env(POSTGRES_USER),
        "password": params.get("password") or from_env(POSTGRES_PASSWORD),
        "host": params.get("host") or from_env(POSTGRES_HOST),
        "port": params.get("port") or from_env(POSTGRES_PORT),
        "database": params.get("database") or from_env(POSTGRES_DATABASE),
    }


def extract_all(**kwargs) -> None:
    """
    Extract all assets from Postgres and store the results in CSV files
    """
    output_directory, skip_existing = common_args(kwargs)

    client = PostgresClient(credentials=_credentials(kwargs))

    query_builder = PostgresQueryBuilder()

    storage = LocalStorage(directory=output_directory)

    extractor = SQLExtractionProcessor(
        client=client,
        query_builder=query_builder,
        storage=storage,
    )

    for group in extractable_asset_groups(POSTGRES_ASSETS):
        for asset in group:
            logger.info(f"Extracting `{asset.value.upper()}` ...")
            location = extractor.extract(asset, skip_existing)
            logger.info(f"Results stored to {location}\n")

    write_summary(
        output_directory,
        storage.stored_at_ts,
        client_name=client.name(),
    )
