import logging
import re
from collections.abc import Iterator
from dataclasses import asdict
from itertools import chain

from ...utils import (
    AbstractSourceClient,
    AbstractStorage,
    SafeMode,
)
from ..abstract import (
    CATALOG_ASSETS,
    EXTERNAL_LINEAGE_ASSETS,
    QUERIES_ASSETS,
    VIEWS_ASSETS,
    SQLExtractionProcessor,
    SupportedAssets,
    WarehouseAsset,
    WarehouseAssetGroup,
)
from .query import RedshiftQueryBuilder
from .types import (
    AssembledQuery,
    LongQuery,
    QueryBuffer,
    QueryMetadata,
    QueryPart,
)

logger = logging.getLogger(__name__)

REDSHIFT_ASSETS: SupportedAssets = {
    WarehouseAssetGroup.CATALOG: CATALOG_ASSETS,
    WarehouseAssetGroup.QUERY: QUERIES_ASSETS,
    WarehouseAssetGroup.VIEW_DDL: VIEWS_ASSETS,
    WarehouseAssetGroup.ROLE: (
        WarehouseAsset.USER,
        WarehouseAsset.GROUP,
    ),
    WarehouseAssetGroup.EXTERNAL_LINEAGE: EXTERNAL_LINEAGE_ASSETS,
}


class RedshiftExtractionProcessor(SQLExtractionProcessor):
    """Extraction management for Redshift"""

    def __init__(
        self,
        client: AbstractSourceClient,
        query_builder: RedshiftQueryBuilder,
        storage: AbstractStorage,
        safe_mode: SafeMode | None = None,
    ):
        super().__init__(client, query_builder, storage, safe_mode)
        self.query_builder = query_builder

    @staticmethod
    def _normalize_insert_values(text: str) -> str:
        """Neutralize heavy VALUES payloads on INSERTs."""
        stripped = text.lstrip()
        if stripped.lower().startswith("insert into"):
            return re.sub(
                r"VALUES\s*(.*)$",
                "DEFAULT VALUES",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )
        return text

    def results(self, asset: WarehouseAsset) -> Iterator[dict]:
        """
        Return ready-to-be-exported data
        queries require some dedicated transformation & reconciliation
        """
        if asset == WarehouseAsset.QUERY:
            return self.queries()
        return self._results(asset)

    @staticmethod
    def _reconcile(
        queries_text: Iterator[AssembledQuery],
        queries_metadata: Iterator[dict],
    ) -> Iterator[dict]:
        """
        Reconcile long queries with their metadata.

        First we retrieve the queries metadata that will serve as reference
        Second we match query text with metadata & yield the combination
        """

        metadata = {}

        for query_metadata in queries_metadata:
            _metadata = QueryMetadata(**query_metadata)
            metadata[_metadata.query_id] = _metadata

        for entry in queries_text:
            if entry.query_id in metadata:
                yield {
                    "query_text": entry.text,
                    **asdict(metadata[entry.query_id]),
                }
            else:
                query_id = entry.query_id
                logger.warning(f"Query {query_id} could not be reconciled")

    @staticmethod
    def _assemble_query(entry: QueryBuffer) -> str:
        """reconstruct the full text of the query"""
        ordered_sequences = sorted(entry.parts.keys())
        return "".join(entry.parts[seq] for seq in ordered_sequences)

    def _assemble_all(
        self, query_parts: Iterator[dict]
    ) -> Iterator[AssembledQuery]:
        """
        Rebuild all full query texts from streamed parts.
        Input rows contain:
          - query_id: query identifier
          - text: fragment of the query
          - sequence: order of the fragment
          - sequence_count: total number of fragments for this query
        """
        buffers: dict[str, QueryBuffer] = dict()

        for query_part in query_parts:
            part = QueryPart(**query_part)

            entry = buffers.get(part.query_id)
            if entry is None:
                entry = QueryBuffer(expected=part.sequence_count)
                buffers[part.query_id] = entry

            entry.parts[part.sequence] = part.text

            # Emit as soon as all parts are collected for this query_id
            if len(entry.parts) >= entry.expected:
                full_text = self._assemble_query(entry)
                normalized = self._normalize_insert_values(full_text)
                yield AssembledQuery(query_id=part.query_id, text=normalized)
                del buffers[part.query_id]

        # Flush any remaining buffers (in case extraction was incomplete)
        for query_id, entry in buffers.items():
            full_text = self._assemble_query(entry)
            normalized = self._normalize_insert_values(full_text)
            yield AssembledQuery(query_id=query_id, text=normalized)

    def fetch_long_queries_text(self) -> Iterator[AssembledQuery]:
        """return the reconstructed query text (for long queries only)"""
        # To retrieve query text we cannot use LISTAGG when the query is longer than 65,535 characters.
        _query = self.query_builder.build_long_query(LongQuery.PARTS)
        raw_long_queries = self.fetch(_query)
        return self._assemble_all(raw_long_queries)

    def fetch_long_queries_metadata(self) -> Iterator[dict]:
        """return the metadata associated with long queries"""
        _query = self.query_builder.build_long_query(LongQuery.METADATA)
        return self.fetch(_query)

    def queries(self) -> Iterator[dict]:
        """redshift queries extracted (with metadata)"""
        short_queries = self._results(WarehouseAsset.QUERY)
        raw_long_queries = self.fetch_long_queries_text()
        long_queries_metadata = self.fetch_long_queries_metadata()
        long_queries = self._reconcile(raw_long_queries, long_queries_metadata)

        return chain(short_queries, long_queries)

    def extract(
        self,
        asset: WarehouseAsset,
        skip_existing: bool = False,
    ) -> str:
        """
        Process extraction for the given asset and returns the location of extracted data
        """
        asset_name = asset.value
        if skip_existing and self._storage.exists(asset_name):
            logger.info("Skipped, file already exists")
            return self._storage.path(asset_name)

        try:
            data = self.results(asset)
            return self._storage.put(asset_name, data)
        finally:
            self._client.close(dispose=True)
