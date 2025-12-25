from ...types import ExternalAsset


class TableauAsset(ExternalAsset):
    """
    Tableau assets
    """

    COLUMN = "columns"
    DASHBOARD = "dashboards"
    DATASOURCE = "datasources"
    FIELD = "fields"
    METRIC = "metrics"
    METRIC_DEFINITION = "metrics_definitions"
    PROJECT = "projects"
    SHEET = "sheets"
    SUBSCRIPTION = "subscriptions"
    TABLE = "tables"
    USAGE = "usage"
    USER = "users"
    WORKBOOK = "workbooks"


# assets that are only available for clients using Tableau Pulse
TABLEAU_PULSE_ASSETS = (
    TableauAsset.METRIC,
    TableauAsset.METRIC_DEFINITION,
    TableauAsset.SUBSCRIPTION,
)
