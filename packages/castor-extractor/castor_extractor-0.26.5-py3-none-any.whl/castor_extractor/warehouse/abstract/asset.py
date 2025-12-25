from enum import Enum

from ...types import ExternalAsset, classproperty


class WarehouseAsset(ExternalAsset):
    """Assets that can be extracted from warehouses"""

    ADDITIONAL_COLUMN_LINEAGE = "additional_column_lineage"
    ADDITIONAL_TABLE_LINEAGE = "additional_table_lineage"
    COLUMN = "column"
    COLUMN_LINEAGE = "column_lineage"  # specific to snowflake
    DATABASE = "database"
    EXTERNAL_COLUMN_LINEAGE = "external_column_lineage"
    EXTERNAL_TABLE_LINEAGE = "external_table_lineage"
    GRANT_TO_ROLE = "grant_to_role"
    GRANT_TO_USER = "grant_to_user"
    GROUP = "group"
    QUERY = "query"
    ROLE = "role"
    SCHEMA = "schema"
    TABLE = "table"
    FUNCTION = "function"
    USER = "user"
    VIEW_DDL = "view_ddl"

    @classproperty
    def optional(cls) -> set["WarehouseAsset"]:
        return {
            WarehouseAsset.ADDITIONAL_COLUMN_LINEAGE,
            WarehouseAsset.ADDITIONAL_TABLE_LINEAGE,
            WarehouseAsset.EXTERNAL_COLUMN_LINEAGE,
            WarehouseAsset.EXTERNAL_TABLE_LINEAGE,
            WarehouseAsset.FUNCTION,
        }


class WarehouseAssetGroup(Enum):
    """Groups of assets that can be extracted together"""

    ADDITIONAL_LINEAGE = "additional_lineage"
    CATALOG = "catalog"
    EXTERNAL_LINEAGE = "external_lineage"
    FUNCTION = "function"
    QUERY = "query"
    ROLE = "role"
    SNOWFLAKE_LINEAGE = "snowflake_lineage"
    VIEW_DDL = "view_ddl"


# tuple of supported assets for each group (depends on the technology)
SupportedAssets = dict[WarehouseAssetGroup, tuple[WarehouseAsset, ...]]

# shared by all technologies
CATALOG_ASSETS = (
    WarehouseAsset.DATABASE,
    WarehouseAsset.SCHEMA,
    WarehouseAsset.TABLE,
    WarehouseAsset.COLUMN,
)

# shared by technologies supporting queries
FUNCTIONS_ASSETS = (WarehouseAsset.FUNCTION,)
QUERIES_ASSETS = (WarehouseAsset.QUERY,)
VIEWS_ASSETS = (WarehouseAsset.VIEW_DDL,)

QUERIES_ASSET_GROUPS = (
    WarehouseAssetGroup.QUERY,
    WarehouseAssetGroup.VIEW_DDL,
)

EXTERNAL_LINEAGE_ASSETS = (
    WarehouseAsset.EXTERNAL_COLUMN_LINEAGE,
    WarehouseAsset.EXTERNAL_TABLE_LINEAGE,
)

ADDITIONAL_LINEAGE_ASSETS = (
    WarehouseAsset.ADDITIONAL_COLUMN_LINEAGE,
    WarehouseAsset.ADDITIONAL_TABLE_LINEAGE,
)

NON_EXTRACTABLE_ASSETS = {WarehouseAssetGroup.EXTERNAL_LINEAGE}


def extractable_asset_groups(
    supported_assets: SupportedAssets,
) -> list[tuple[WarehouseAsset, ...]]:
    """
    helper function to differentiate
    extractable assets vs supported (ingest-able) assets
    """
    groups = set(supported_assets).difference(NON_EXTRACTABLE_ASSETS)
    extractable: set[tuple[WarehouseAsset, ...]] = {
        supported_assets[group] for group in groups
    }
    return list(extractable)
