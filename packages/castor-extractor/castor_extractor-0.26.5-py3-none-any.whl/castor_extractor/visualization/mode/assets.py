from ...types import ExternalAsset


class ModeAnalyticsAsset(ExternalAsset):
    """Mode Analytics assets"""

    DATASOURCE = "data_sources"
    REPORT = "reports"
    COLLECTION = "spaces"  # legacy name, still valid in the API
    MEMBER = "user"
    QUERY = "queries"


ASSETS_WITH_OWNER = (
    ModeAnalyticsAsset.COLLECTION,
    ModeAnalyticsAsset.REPORT,
)


EXPORTED_FIELDS = {
    ModeAnalyticsAsset.DATASOURCE: (
        "id",
        "token",
        "name",
        "host",
        "display_name",
        "description",
        "database",
        "provider",
        "vendor",
        "adapter",
        "created_at",
        "public",
        "queryable",
    ),
    ModeAnalyticsAsset.MEMBER: (
        "id",
        "token",
        "username",
        "name",
        "email",
        "created_at",
    ),
    ModeAnalyticsAsset.REPORT: (
        "id",
        "token",
        "name",
        "description",
        "type",
        "archived",
        "space_token",
        "public",
        "created_at",
        "updated_at",
        "published_at",
        "edited_at",
        "is_embedded",
        "query_count",
        "chart_count",
        "view_count",
        "creator",
    ),
    ModeAnalyticsAsset.QUERY: (
        "id",
        "token",
        "name",
        "data_source_id",
        "raw_query",
        "report_token",
    ),
    ModeAnalyticsAsset.COLLECTION: (
        "id",
        "token",
        "space_type",
        "name",
        "description",
        "state",
        "default_access_level",
        "creator",
    ),
}
