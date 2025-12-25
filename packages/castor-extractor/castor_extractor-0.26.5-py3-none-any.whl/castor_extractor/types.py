from abc import ABC
from enum import Enum
from typing import Literal, TypedDict


class CsvOptions(TypedDict):
    delimiter: str
    quoting: Literal[1]
    quotechar: str


class classproperty(property):
    """
    Allow combination of @classmethod + @property
    https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    """

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


class ExternalAsset(Enum):
    """
    Abstract class representing External Assets which can be extracted

    Enum's NAME identifies the asset.
        Example: TableauAsset.WORKBOOK

    Enum's VALUE gives the file name.
        Example: workbooks.json

    """

    __metaclass__ = ABC

    @classproperty
    def optional(cls) -> set["ExternalAsset"]:
        """
        Returns the assets that are not necessarily extracted/pushed.
        Example:
        {
            WarehouseAsset.EXTERNAL_TABLE_LINEAGE,
            WarehouseAsset.EXTERNAL_COLUMN_LINEAGE,
        }
        """
        return set()

    @classproperty
    def mandatory(cls) -> set["ExternalAsset"]:
        """
        Returns the assets that must always be provided.
        """
        return {item for item in cls if item not in cls.optional}  # type: ignore
