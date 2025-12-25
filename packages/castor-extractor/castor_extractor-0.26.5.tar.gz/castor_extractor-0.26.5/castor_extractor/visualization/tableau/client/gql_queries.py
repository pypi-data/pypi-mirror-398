from ..assets import TableauAsset

QUERY_TEMPLATE = """
{{
  {resource}Connection(first: {first}, offset: {offset}, filter: {filter}) {{
    nodes {{ {fields}
    }}
    pageInfo {{
      hasNextPage
      endCursor
    }}
    totalCount
  }}
}}
"""

_COLUMNS_QUERY = """
downstreamDashboards { id }
downstreamFields {
    id
    __typename
    datasource { id }
}
downstreamWorkbooks { id }
id
name
table { id }
"""

_DASHBOARDS_QUERY = """
createdAt
id
name
path
tags { name }
updatedAt
workbook { id }
"""

_DATASOURCES_QUERY = """
__typename
downstreamDashboards { id }
downstreamWorkbooks { id }
id
name
... on PublishedDatasource {
    description
    luid
    owner { luid }
    site { name }
    tags { name }
    uri
}
"""

_TABLES_QUERY = """
__typename
downstreamDashboards { id }
downstreamDatasources { id }
downstreamWorkbooks { id }
id
name
... on DatabaseTable {
    fullName
    schema
    database {
        connectionType
        id
        name
    }
}
... on CustomSQLTable {
    query
    database {
        connectionType
        id
        name
    }
}
"""


_WORKBOOKS_QUERY = """
createdAt
description
embeddedDatasources { id }
id
luid
name
owner { luid }
site { name }
tags { name }
updatedAt
uri
"""

_FIELDS_QUERY = """
__typename
datasource { id }
description
downstreamDashboards { id }
downstreamWorkbooks { id }
folderName
id
name
dataType
role
"""


_FIELDS_QUERY_WITH_COLUMNS = f"""
{_FIELDS_QUERY}
columns {{
    name
   table {{ name }}
}}
"""

_SHEETS_QUERY = """
containedInDashboards { id }
createdAt
id
index
name
updatedAt
upstreamFields { name }
workbook { id }
"""

_LIGHT_TABLES_QUERY = """
id
... on DatabaseTable { fullName }
"""

_LIGHT_COLUMNS_QUERY = """
id
columns { id }
"""

LIGHT_GQL_QUERIES: dict[TableauAsset, tuple[str, str, int]] = {
    # both queries hit the "Tables" endpoint, but the second one also fetch
    # the list of columns
    TableauAsset.TABLE: ("tables", _LIGHT_TABLES_QUERY, 1000),
    # fetching tables + columns is heavier for the metadata API
    # we must reduce the page-size otherwise we get timeouts
    TableauAsset.COLUMN: ("tables", _LIGHT_COLUMNS_QUERY, 100),
}

GQL_QUERIES: dict[TableauAsset, tuple[str, str]] = {
    TableauAsset.COLUMN: ("columns", _COLUMNS_QUERY),
    TableauAsset.DASHBOARD: ("dashboards", _DASHBOARDS_QUERY),
    TableauAsset.DATASOURCE: ("datasources", _DATASOURCES_QUERY),
    TableauAsset.SHEET: ("sheets", _SHEETS_QUERY),
    TableauAsset.TABLE: ("tables", _TABLES_QUERY),
    TableauAsset.WORKBOOK: ("workbooks", _WORKBOOKS_QUERY),
}

FIELDS_QUERIES = (
    ("binFields", _FIELDS_QUERY),
    ("calculatedFields", _FIELDS_QUERY),
    ("columnFields", _FIELDS_QUERY_WITH_COLUMNS),
    ("groupFields", _FIELDS_QUERY),
)
