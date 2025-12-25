import logging

from ...utils import LocalStorage, from_env, write_summary
from ..abstract import (
    CATALOG_ASSETS,
    EXTERNAL_LINEAGE_ASSETS,
    QUERIES_ASSETS,
    VIEWS_ASSETS,
    SupportedAssets,
    WarehouseAsset,
    WarehouseAssetGroup,
    common_args,
    extractable_asset_groups,
)
from .client import RedshiftClient
from .processor import RedshiftExtractionProcessor
from .query import RedshiftQueryBuilder

logger = logging.getLogger(__name__)

REDSHIFT_ASSETS: SupportedAssets = {
    WarehouseAssetGroup.CATALOG: CATALOG_ASSETS,
    WarehouseAssetGroup.QUERY: QUERIES_ASSETS,
    WarehouseAssetGroup.VIEW_DDL: VIEWS_ASSETS,
    WarehouseAssetGroup.ROLE: (
        WarehouseAsset.USER,
        WarehouseAsset.GROUP,
    ),
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
}

REDSHIFT_USER = "CASTOR_REDSHIFT_USER"
REDSHIFT_PASSWORD = "CASTOR_REDSHIFT_PASSWORD"  # noqa: S105
REDSHIFT_HOST = "CASTOR_REDSHIFT_HOST"
REDSHIFT_PORT = "CASTOR_REDSHIFT_PORT"
REDSHIFT_DATABASE = "CASTOR_REDSHIFT_DATABASE"
REDSHIFT_SERVERLESS = "CASTOR_REDSHIFT_SERVERLESS"


def _credentials(params: dict) -> dict:
    """extract Redshift credentials"""

    return {
        "user": params.get("user") or from_env(REDSHIFT_USER),
        "password": params.get("password") or from_env(REDSHIFT_PASSWORD),
        "host": params.get("host") or from_env(REDSHIFT_HOST),
        "port": params.get("port") or from_env(REDSHIFT_PORT),
        "database": params.get("database") or from_env(REDSHIFT_DATABASE),
    }


def _query_builder(params: dict) -> RedshiftQueryBuilder:
    env_parameter = from_env(REDSHIFT_SERVERLESS, allow_missing=True)
    from_env_ = str(env_parameter).lower() == "true"
    from_params_ = params.get("serverless", False)
    is_serverless = from_params_ or from_env_
    return RedshiftQueryBuilder(is_serverless=is_serverless)


def extract_all(**kwargs) -> None:
    """
    Extract all assets from Redshift and store the results in CSV files
    """
    output_directory, skip_existing = common_args(kwargs)

    client = RedshiftClient(credentials=_credentials(kwargs))

    query_builder = _query_builder(kwargs)

    storage = LocalStorage(directory=output_directory)

    extractor = RedshiftExtractionProcessor(
        client=client,
        query_builder=query_builder,
        storage=storage,
    )

    for group in extractable_asset_groups(REDSHIFT_ASSETS):
        for asset in group:
            logger.info(f"Extracting `{asset.value.upper()}` ...")
            location = extractor.extract(asset, skip_existing)
            logger.info(f"Results stored to {location}\n")

    write_summary(
        output_directory,
        storage.stored_at_ts,
        client_name=client.name(),
    )
