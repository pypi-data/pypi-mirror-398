from ...types import ExternalAsset, classproperty


class PowerBiAsset(ExternalAsset):
    """PowerBi assets"""

    ACTIVITY_EVENTS = "activity_events"
    DASHBOARDS = "dashboards"
    DATASETS = "datasets"
    DATASET_FIELDS = "dataset_fields"
    DATASET_RELATIONSHIPS = "dataset_relationships"
    METADATA = "metadata"
    PAGES = "pages"
    REPORTS = "reports"
    TABLES = "tables"
    TILES = "tiles"
    USERS = "users"

    @classproperty
    def optional(cls) -> set["PowerBiAsset"]:
        return {
            PowerBiAsset.DATASET_FIELDS,
            PowerBiAsset.DATASET_RELATIONSHIPS,
            PowerBiAsset.PAGES,
            PowerBiAsset.TABLES,
            PowerBiAsset.TILES,
            PowerBiAsset.USERS,
        }
