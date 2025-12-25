from ...types import ExternalAsset, classproperty


class LookerStudioAsset(ExternalAsset):
    ASSETS = "assets"
    SOURCE_QUERIES = "source_queries"
    VIEW_ACTIVITY = "view_activity"

    @classproperty
    def optional(cls) -> set["LookerStudioAsset"]:
        return {LookerStudioAsset.VIEW_ACTIVITY}
