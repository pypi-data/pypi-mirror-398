from enum import Enum


class LineageEntity(Enum):
    """Entities that can be linked in Databricks lineage"""

    COLUMN = "COLUMN"
    TABLE = "TABLE"


class TagEntity(Enum):
    """Entities that can be tagged in Databricks"""

    COLUMN = "COLUMN"
    TABLE = "TABLE"
