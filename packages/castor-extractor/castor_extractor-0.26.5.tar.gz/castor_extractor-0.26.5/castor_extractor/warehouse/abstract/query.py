import inspect
import os
from abc import ABC, abstractmethod

from ...utils import ExtractionQuery
from .asset import WarehouseAsset
from .time_filter import TimeFilter

TIME_FILTERED_ASSETS = (
    WarehouseAsset.COLUMN_LINEAGE,
    WarehouseAsset.QUERY,
)

QUERIES_DIR = "queries"


class AssetNotSupportedError(NotImplementedError):
    def __init__(self, asset: WarehouseAsset, builder_name: str):
        msg = f"Extraction of {asset} is not supported by {builder_name}"
        super().__init__(msg)


class AbstractQueryBuilder(ABC):
    """
    Build queries necessary to extract warehouse assets.
    Handle feeding of parameters as well.
    """

    def __init__(
        self,
        time_filter: TimeFilter | None,
        duplicated: tuple[WarehouseAsset, ...] | None = None,
    ):
        self._time_filter = time_filter or TimeFilter.default()
        self._duplicated = duplicated

    def needs_deduplication(self, asset: WarehouseAsset) -> bool:
        if self._duplicated:
            return asset in self._duplicated
        return False

    def file_name(self, asset: WarehouseAsset) -> str:
        """Returns the SQL filename extracting the given asset"""
        return f"{asset.value}.sql"

    def _load_from_file(self, filename: str) -> str:
        """read from a file located in queries directory"""
        root = os.path.dirname(inspect.getfile(self.__class__))
        path = os.path.join(root, QUERIES_DIR, filename)
        with open(path) as f:
            return f.read()

    def load_statement(self, asset: WarehouseAsset) -> str:
        """load SQL statement from file"""
        filename = self.file_name(asset)
        try:
            return self._load_from_file(filename)
        except FileNotFoundError:
            raise AssetNotSupportedError(asset, self.__class__.__name__)

    def build_default(self, asset: WarehouseAsset) -> ExtractionQuery:
        statement = self.load_statement(asset)
        params: dict = {}
        if asset in TIME_FILTERED_ASSETS:
            params = self._time_filter.to_dict()

        return ExtractionQuery(statement, params)

    @abstractmethod
    def build(self, asset: WarehouseAsset) -> list[ExtractionQuery]:
        """
        Build the Query allowing extraction of the given asset
        - Most of the time, returns a single query
        - Sometimes we must stitch several queries, hence the list
        """
