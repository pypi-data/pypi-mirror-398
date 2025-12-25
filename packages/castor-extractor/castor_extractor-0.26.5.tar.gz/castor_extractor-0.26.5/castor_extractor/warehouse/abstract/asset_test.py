from .asset import (
    EXTERNAL_LINEAGE_ASSETS,
    SupportedAssets,
    WarehouseAsset,
    WarehouseAssetGroup,
    extractable_asset_groups,
)

COOL_TECHNOLOGY_ASSETS: SupportedAssets = {
    WarehouseAssetGroup.CATALOG: (
        WarehouseAsset.DATABASE,
        WarehouseAsset.SCHEMA,
    ),
    WarehouseAssetGroup.ROLE: (WarehouseAsset.USER,),
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
}


def test_extractable_asset_groups():
    all_assets = set()
    for group in extractable_asset_groups(COOL_TECHNOLOGY_ASSETS):
        all_assets.update(group)

    expected = {
        WarehouseAsset.DATABASE,
        WarehouseAsset.SCHEMA,
        WarehouseAsset.USER,
    }  # no external lineage
    assert all_assets == expected
