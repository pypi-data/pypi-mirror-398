from ..assets import SalesforceReportingAsset

queries: dict[SalesforceReportingAsset, str] = {
    SalesforceReportingAsset.DASHBOARDS: """
        SELECT
            CreatedBy.Id,
            CreatedDate,
            Description,
            DeveloperName,
            FolderId,
            FolderName,
            Id,
            IsDeleted,
            LastReferencedDate,
            LastViewedDate,
            NamespacePrefix,
            RunningUserId,
            Title,
            Type
        FROM Dashboard
        WHERE IsDeleted = FALSE
    """,
    SalesforceReportingAsset.FOLDERS: """
    SELECT
        DeveloperName,
        Id,
        Name,
        NamespacePrefix,
        ParentId,
        Type
    FROM Folder
    WHERE Type IN ('Dashboard', 'Report')
    """,
    SalesforceReportingAsset.REPORTS: """
        SELECT
            CreatedBy.Id,
            Description,
            DeveloperName,
            FolderName,
            Format,
            Id,
            IsDeleted,
            LastReferencedDate,
            LastRunDate,
            LastViewedDate,
            Name,
            NamespacePrefix,
            OwnerId
        FROM Report
        WHERE IsDeleted = FALSE
    """,
    SalesforceReportingAsset.USERS: """
        SELECT
            Id,
            Email,
            FirstName,
            LastName,
            CreatedDate
        FROM User
        WHERE UserType = 'Standard'
    """,
    SalesforceReportingAsset.DASHBOARD_COMPONENTS: """
        SELECT
            CustomReportId,
            DashboardId,
            Name
        FROM DashboardComponent
    """,
}
