class DatabricksEndpointFactory:
    @classmethod
    def tables(cls):
        return "api/2.1/unity-catalog/tables"

    @classmethod
    def schemas(cls):
        return "api/2.1/unity-catalog/schemas"

    @classmethod
    def databases(cls):
        return "api/2.1/unity-catalog/catalogs"

    @classmethod
    def table_lineage(cls):
        return "api/2.0/lineage-tracking/table-lineage"

    @classmethod
    def column_lineage(cls):
        return "api/2.0/lineage-tracking/column-lineage"

    @classmethod
    def queries(cls):
        return "api/2.0/sql/history/queries"

    @classmethod
    def users(cls):
        return "api/2.0/preview/scim/v2/Users"
