from ...types import ExternalAsset


class CoalesceAsset(ExternalAsset):
    """Coalesce assets"""

    NODES = "nodes"


class CoalesceQualityAsset(ExternalAsset):
    """
    Coalesce Quality Assets
    Remark: having a dedicated Enum for Quality simplifies the process of
    searching pushed files
    """

    NODES = "nodes"
    RUN_RESULTS = "run_results"
