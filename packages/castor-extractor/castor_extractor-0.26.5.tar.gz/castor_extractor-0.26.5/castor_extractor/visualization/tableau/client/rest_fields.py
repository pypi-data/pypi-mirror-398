from ..assets import TableauAsset

# list of fields to pick in REST API or TSC responses
REST_FIELDS: dict[TableauAsset, set[str]] = {
    TableauAsset.DATASOURCE: {
        "id",
        "project_id",
        "webpage_url",
    },
    TableauAsset.METRIC: {
        "id",
        "definition_id",
    },
    TableauAsset.METRIC_DEFINITION: {
        "metadata",
        "specification",
    },
    TableauAsset.PROJECT: {
        "description",
        "id",
        "name",
        "parent_id",
    },
    TableauAsset.SUBSCRIPTION: {
        "follower",
        "id",
        "metric_id",
    },
    TableauAsset.USAGE: {
        "name",
        "total_views",
        "workbook_id",
    },
    TableauAsset.USER: {
        "email",
        "fullname",
        "id",
        "name",
        "site_role",
    },
    TableauAsset.WORKBOOK: {
        "id",
        "project_id",
    },
}
