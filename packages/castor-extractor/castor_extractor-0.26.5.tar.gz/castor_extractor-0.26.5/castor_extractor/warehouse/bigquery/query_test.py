from ..abstract import WarehouseAsset
from .query import INCOMPATIBLE_WITH_OMNI, _omni_compatible


def test__omni_compatible():
    # asset that is incompatible with omni
    asset = next(iter(INCOMPATIBLE_WITH_OMNI))

    regions = {
        ("p1", "us-central1"),
        ("p1", "aws-us-east-1"),
        ("p1", "azure-europe-west3"),
        ("p2", "europe-west1"),
    }

    filtered = _omni_compatible(regions, asset)

    # non-omni locations should remain
    assert ("p1", "us-central1") in filtered
    assert ("p2", "europe-west1") in filtered

    # omni locations must be removed
    assert ("p1", "aws-us-east-1") not in filtered
    assert ("p1", "azure-europe-west3") not in filtered

    # pick an asset that is NOT in the incompatible list
    compatible_asset = next(
        a for a in WarehouseAsset if a not in INCOMPATIBLE_WITH_OMNI
    )

    regions = {
        ("p1", "us-central1"),
        ("p1", "aws-us-east-1"),
        ("p1", "azure-europe-west3"),
    }

    filtered = _omni_compatible(regions, compatible_asset)

    # nothing should be filtered out
    assert filtered == regions
