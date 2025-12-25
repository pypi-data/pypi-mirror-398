from ...types import ExternalAsset


class SalesforceReportingAsset(ExternalAsset):
    """Salesforce Reporting assets"""

    DASHBOARDS = "dashboards"
    DASHBOARD_COMPONENTS = "dashboard_components"
    FOLDERS = "folders"
    REPORTS = "reports"
    REPORTS_METADATA = "reports_metadata"
    USERS = "users"
