import logging

from ...exceptions import (
    NoDatabaseProvidedException,
)
from ...utils import LocalStorage, from_env, write_summary
from ..abstract import (
    CATALOG_ASSETS,
    EXTERNAL_LINEAGE_ASSETS,
    FUNCTIONS_ASSETS,
    QUERIES_ASSETS,
    VIEWS_ASSETS,
    SQLExtractionProcessor,
    SupportedAssets,
    WarehouseAsset,
    WarehouseAssetGroup,
    common_args,
    extractable_asset_groups,
)
from .client import SnowflakeClient
from .query_builder import SnowflakeQueryBuilder

logger = logging.getLogger(__name__)

SNOWFLAKE_ASSETS: SupportedAssets = {
    WarehouseAssetGroup.CATALOG: CATALOG_ASSETS,
    WarehouseAssetGroup.FUNCTION: FUNCTIONS_ASSETS,
    WarehouseAssetGroup.QUERY: QUERIES_ASSETS,
    WarehouseAssetGroup.VIEW_DDL: VIEWS_ASSETS,
    WarehouseAssetGroup.ROLE: (WarehouseAsset.USER,),
    WarehouseAssetGroup.SNOWFLAKE_LINEAGE: (WarehouseAsset.COLUMN_LINEAGE,),
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
}

SNOWFLAKE_ACCOUNT = "CASTOR_SNOWFLAKE_ACCOUNT"
SNOWFLAKE_USER = "CASTOR_SNOWFLAKE_USER"
SNOWFLAKE_PASSWORD = "CASTOR_SNOWFLAKE_PASSWORD"  # noqa: S105
SNOWFLAKE_PRIVATE_KEY = "CASTOR_SNOWFLAKE_PRIVATE_KEY"
SNOWFLAKE_INSECURE_MODE = "CASTOR_SNOWFLAKE_INSECURE_MODE"


def _credentials(params: dict) -> dict:
    """extract Snowflake credentials"""
    password = params.get("password") or from_env(SNOWFLAKE_PASSWORD, True)
    private_key = params.get("private_key") or from_env(
        SNOWFLAKE_PRIVATE_KEY, True
    )
    insecure_mode = (
        params.get("insecure_mode")
        or from_env(SNOWFLAKE_INSECURE_MODE, allow_missing=True)
        or False
    )
    common = {
        "account": params.get("account") or from_env(SNOWFLAKE_ACCOUNT),
        "user": params.get("user") or from_env(SNOWFLAKE_USER),
        "insecure_mode": insecure_mode,
    }
    if password:
        return {**common, "password": password}
    if private_key:
        return {**common, "private_key": private_key}

    raise ValueError("missing password or private key")


def _get_database_names(
    extractor: SQLExtractionProcessor, query_builder: SnowflakeQueryBuilder
) -> set[str]:
    db_query = query_builder.build(WarehouseAsset.DATABASE)
    databases = list(extractor.fetch(db_query[0]))
    return {db["database_name"] for db in databases}


def extract_all(**kwargs) -> None:
    """
    Extract all assets from Snowflake and store the results in CSV files
    """
    output_directory, skip_existing = common_args(kwargs)
    client = SnowflakeClient(
        credentials=_credentials(kwargs),
        warehouse=kwargs.get("warehouse"),
        role=kwargs.get("role"),
    )

    query_builder = SnowflakeQueryBuilder(
        db_allowed=kwargs.get("db_allowed"),
        db_blocked=kwargs.get("db_blocked"),
        query_blocked=kwargs.get("query_blocked"),
        fetch_transient=kwargs.get("fetch_transient"),
    )

    storage = LocalStorage(directory=output_directory)

    extractor = SQLExtractionProcessor(
        client=client,
        query_builder=query_builder,
        storage=storage,
    )

    database_names = _get_database_names(extractor, query_builder)
    if not database_names:
        raise NoDatabaseProvidedException

    logger.info(f"Available databases: {database_names}\n")

    for group in extractable_asset_groups(SNOWFLAKE_ASSETS):
        for asset in group:
            logger.info(f"Extracting `{asset.value.upper()}` ...")
            location = extractor.extract(asset, skip_existing)
            logger.info(f"Results stored to {location}\n")

    write_summary(
        output_directory,
        storage.stored_at_ts,
        client_name=client.name(),
    )
