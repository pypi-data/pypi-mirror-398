class SigmaEndpointFactory:
    """Wrapper class around all endpoints we're using"""

    DATAMODELS = "dataModels"
    DATASETS = "datasets"
    FILES = "files"
    MEMBERS = "members"
    WORKBOOKS = "workbooks"

    @classmethod
    def authentication(cls) -> str:
        return "v2/auth/token"

    @classmethod
    def connection_path(cls, inode_id: str) -> str:
        return f"v2/connections/paths/{inode_id}"

    @classmethod
    def datamodels(cls) -> str:
        return f"v2/{cls.DATAMODELS}"

    @classmethod
    def datamodel_sources(cls, datamodel_id: str) -> str:
        return f"v2/{cls.DATAMODELS}/{datamodel_id}/sources"

    @classmethod
    def datasets(cls) -> str:
        return f"v2/{cls.DATASETS}"

    @classmethod
    def dataset_sources(cls, dataset_id: str) -> str:
        return f"v2/{cls.DATASETS}/{dataset_id}/sources"

    @classmethod
    def elements(cls, workbook_id: str, page_id: str) -> str:
        return f"v2/{cls.WORKBOOKS}/{workbook_id}/pages/{page_id}/elements"

    @classmethod
    def files(cls) -> str:
        return f"v2/{cls.FILES}"

    @classmethod
    def lineage(cls, workbook_id: str, element_id: str) -> str:
        return f"v2/{cls.WORKBOOKS}/{workbook_id}/lineage/elements/{element_id}"

    @classmethod
    def members(cls) -> str:
        return f"v2/{cls.MEMBERS}"

    @classmethod
    def pages(cls, workbook_id: str) -> str:
        return f"v2/{cls.WORKBOOKS}/{workbook_id}/pages"

    @classmethod
    def queries(cls, workbook_id: str) -> str:
        return f"v2/{cls.WORKBOOKS}/{workbook_id}/queries"

    @classmethod
    def workbooks(cls) -> str:
        return f"v2/{cls.WORKBOOKS}"

    @classmethod
    def workbook_sources(cls, workbook_id: str) -> str:
        return f"v2/{cls.WORKBOOKS}/{workbook_id}/sources"
