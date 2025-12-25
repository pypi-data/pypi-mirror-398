import logging

from ..abstract import (
    AbstractQueryBuilder,
    ExtractionQuery,
    TimeFilter,
    WarehouseAsset,
)
from .types import SetTwoString

logger = logging.getLogger(__name__)

# Those queries must be formatted with {region}
REGION_REQUIRED = (
    WarehouseAsset.COLUMN,
    WarehouseAsset.DATABASE,
    WarehouseAsset.QUERY,
    WarehouseAsset.SCHEMA,
    WarehouseAsset.TABLE,
    WarehouseAsset.USER,
)

# extracting these assets on Omni location will fail with error:
# > Unsupported processing region in the INFORMATION_SCHEMA
INCOMPATIBLE_WITH_OMNI = (
    WarehouseAsset.QUERY,
    WarehouseAsset.USER,
)

# Some clients use empty projects (no datasets) to run their SQL queries
# The extended regions is a combination of all regions with all projects
# It allows to extract those queries which were left apart before
EXTENDED_REGION_REQUIRED = (WarehouseAsset.QUERY,)

# Those queries must be formatted with {dataset}
DATASET_REQUIRED = (WarehouseAsset.VIEW_DDL,)

# Those queries must be de-duplicated
# The usage of DISTINCT in the query is not enough
# because we stitch several queries results
BIGQUERY_DUPLICATES = (
    WarehouseAsset.DATABASE,
    WarehouseAsset.USER,
)

SHARDED_ASSETS = (WarehouseAsset.TABLE, WarehouseAsset.COLUMN)
SHARDED_FILE_PATH = "cte/sharded.sql"

# https://docs.cloud.google.com/bigquery/docs/locations#omni-loc
OMNI_LOCATION_PREFIXES = (
    "aws",
    "azure",
)


def _database_formatted(datasets: SetTwoString) -> str:
    databases = {db for _, db in datasets}
    if not databases:
        # when no datasets are provided condition should pass
        return "(NULL)"
    formatted = ", ".join([f"'{db}'" for db in databases])
    return f"({formatted})"


def _is_omni(location: str) -> bool:
    return any(
        location.startswith(f"{prefix}-") for prefix in OMNI_LOCATION_PREFIXES
    )


def _omni_compatible(
    regions: SetTwoString,
    asset: WarehouseAsset,
) -> SetTwoString:
    """
    Some assets (e.g., SQL queries, Users, ...) are not compatible with external
    locations (Omni)
    https://docs.cloud.google.com/bigquery/docs/locations#omni-loc

    When such an asset is encountered, any region whose location correspond to
    an Omni environment is excluded.
    """
    omni_blocked = asset in INCOMPATIBLE_WITH_OMNI
    return {
        (project, location)
        for project, location in regions
        if not (omni_blocked and _is_omni(location))
    }


class BigQueryQueryBuilder(AbstractQueryBuilder):
    """
    Builds queries to extract assets from BigQuery.
    Generate multiple queries to support multi-regions
    """

    def __init__(
        self,
        regions: SetTwoString,
        datasets: SetTwoString,
        time_filter: TimeFilter | None = None,
        sync_tags: bool | None = False,
        extended_regions: SetTwoString | None = None,
    ):
        super().__init__(
            time_filter=time_filter,
            duplicated=BIGQUERY_DUPLICATES,
        )
        self._regions = regions
        self._datasets = datasets
        self._sync_tags = sync_tags
        self._extended_regions = extended_regions or regions

    @staticmethod
    def _format(query: ExtractionQuery, values: dict) -> ExtractionQuery:
        return ExtractionQuery(
            statement=query.statement.format(**values),
            params=query.params,
        )

    def file_name(self, asset: WarehouseAsset) -> str:
        """
        Returns the SQL filename extracting the given asset.
        Overrides the default behaviour - handle table tags for BigQuery
        """
        if asset == WarehouseAsset.TABLE and self._sync_tags:
            # Reading `INFORMATION_SCHEMA.SCHEMATA_OPTIONS` requires specific permissions.
            # Synchronization of tags is only activated when credentials are sufficient.
            return f"{asset.value}_with_tags.sql"

        return f"{asset.value}.sql"

    def load_statement(self, asset: WarehouseAsset) -> str:
        """load sql statement from file"""
        statement = super().load_statement(asset)

        if asset not in SHARDED_ASSETS:
            return statement

        sharded_statement = self._load_from_file(SHARDED_FILE_PATH)
        return statement.format(sharded_statement=sharded_statement)

    def _get_regions(self, asset: WarehouseAsset) -> SetTwoString:
        """
        Return the set of (project, location) tuples in which the given asset
        may be processed.
        """
        candidate_regions = (
            self._extended_regions
            if asset in EXTENDED_REGION_REQUIRED
            else self._regions
        )
        return _omni_compatible(candidate_regions, asset)

    def build(self, asset: WarehouseAsset) -> list[ExtractionQuery]:
        """
        It would be easier to stitch data directly in the query statement (UNION ALL).
        Unfortunately, querying INFORMATION_SCHEMA on multiple regions
          at the same time gives partial result (seems like a BigQuery bug)
        This weird behaviour forces us to
          - run one query per tuple(project, region)
          -  stitch data afterwards.
        """
        logger.info(f"Building queries for extracting {asset}")
        query = super().build_default(asset)

        if asset in REGION_REQUIRED:
            regions = self._get_regions(asset)

            logger.info(
                f"\tWill run queries with following region params: {regions}",
            )
            return [
                self._format(query, {"project": project, "region": region})
                for project, region in regions
            ]

        if asset in DATASET_REQUIRED:
            logger.info(
                f"\tWill run queries with following dataset params: {self._datasets}",
            )
            return [
                self._format(query, {"project": project, "dataset": dataset})
                for project, dataset in self._datasets
            ]

        return [query]
