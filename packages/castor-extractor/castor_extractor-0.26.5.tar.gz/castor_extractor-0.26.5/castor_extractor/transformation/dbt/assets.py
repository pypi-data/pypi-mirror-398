from ...types import ExternalAsset


class DbtAsset(ExternalAsset):
    """dbt assets"""

    MANIFEST = "manifest"
    RUN_RESULTS = "run_results"
