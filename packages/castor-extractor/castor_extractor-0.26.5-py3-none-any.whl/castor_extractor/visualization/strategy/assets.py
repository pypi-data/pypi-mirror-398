from ...types import ExternalAsset, classproperty


class StrategyAsset(ExternalAsset):
    """Strategy assets that can be extracted"""

    ATTRIBUTE = "attribute"
    COLUMN = "column"
    CUBE = "cube"
    DASHBOARD = "dashboard"
    DOCUMENT = "document"
    FACT = "fact"
    LOGICAL_TABLE = "logical_table"
    METRIC = "metric"
    REPORT = "report"
    USER = "user"

    @classproperty
    def optional(cls) -> set["StrategyAsset"]:
        return {StrategyAsset.COLUMN}
