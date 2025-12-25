import logging
from collections.abc import Callable, Iterator
from typing import Any
from urllib.parse import urlparse

from mstrio.connection import Connection  # type: ignore
from mstrio.helpers import IServerError  # type: ignore
from mstrio.modeling import (  # type: ignore
    Attribute,
    LogicalTable,
    PhysicalTable,
    PhysicalTableType,
    list_attributes,
    list_facts,
    list_logical_tables,
    list_metrics,
)
from mstrio.project_objects import (  # type: ignore
    Report,
    list_dashboards,
    list_documents,
    list_olap_cubes,
    list_reports,
)
from mstrio.server import Environment  # type: ignore
from mstrio.users_and_groups import User, list_users  # type: ignore
from mstrio.utils.entity import Entity  # type: ignore

from ..assets import StrategyAsset
from .credentials import StrategyCredentials
from .properties import (
    column_properties,
    format_url,
    list_dependencies,
    lookup_table_id,
    safe_get_property,
)

logger = logging.getLogger(__name__)


class StrategyClient:
    """Connect to Strategy through mstrio-py and fetch main assets."""

    def __init__(self, credentials: StrategyCredentials):
        self.base_url = credentials.base_url
        self.connection = Connection(
            base_url=self.base_url,
            username=credentials.username,
            password=credentials.password,
            verbose=False,
        )

        self.hostname = urlparse(self.base_url).hostname

        if credentials.project_ids:
            self.project_ids = credentials.project_ids
        else:
            env = Environment(connection=self.connection)
            self.project_ids = [project.id for project in env.list_projects()]

    def close(self):
        self.connection.close()

    def _common_entity_properties(
        self,
        entity: Entity,
        project_id: str,
        with_url: bool = True,
        with_description: bool = True,
    ) -> dict:
        """
        Returns the entity's properties, including its dependencies
        and optional URL and/or description.
        """
        dependencies = list_dependencies(entity)
        owner_id = entity.owner.id if isinstance(entity.owner, User) else None
        properties = {
            "dependencies": dependencies,
            "id": entity.id,
            "location": entity.location,
            "name": entity.name,
            "owner_id": owner_id,
            "project_id": project_id,
            "subtype": entity.subtype,
            "type": entity.type.value,
        }

        if with_url:
            assert self.hostname
            properties["url"] = format_url(
                entity=entity, hostname=self.hostname
            )

        if with_description:
            properties["description"] = safe_get_property(entity, "description")

        return properties

    def _attributes_properties(
        self, attribute: Attribute, project_id: str
    ) -> dict[str, Any]:
        """
        Attributes have a lookup table, which we need to compute the table lineage.
        """
        return {
            **self._common_entity_properties(
                attribute,
                project_id=project_id,
                with_url=False,
            ),
            "lookup_table_id": lookup_table_id(attribute),
        }

    def _physical_table_properties(
        self, table: PhysicalTable | None
    ) -> dict[str, Any] | None:
        """
        Returns the properties of the physical table, including its columns.
        A physical table can have 1 of these types:
          * "normal": meaning it matches 1 warehouse table
          * "sql": it is based on an SQL statement
        Other types are not supported (and they technically shouldn't be possible.)
        """
        if not table:
            return None

        properties = {
            "id": table.id,
            "name": table.name,
            "type": table.table_type.value,
            "columns": column_properties(table.columns),
        }

        if table.table_type == PhysicalTableType.SQL:
            physical_table = PhysicalTable(
                connection=self.connection,
                id=table.id,
            )
            properties["sql_statement"] = physical_table.sql_statement

        elif table.table_type == PhysicalTableType.NORMAL:
            properties["table_prefix"] = table.table_prefix
            properties["table_name"] = table.table_name

        return properties

    def _logical_table_properties(
        self,
        table: LogicalTable,
        project_id: str,
    ) -> dict[str, Any]:
        """
        Returns properties for:
            * the logical table itself
            * its physical table (though it may not be accessible)
            * the columns of the physical table
        """
        physical_table = safe_get_property(table, "physical_table")
        return {
            "id": table.id,
            "name": table.name,
            "physical_table": self._physical_table_properties(physical_table),
            "project_id": project_id,
        }

    def _report_properties(
        self,
        report: Report,
        project_id: str,
    ) -> dict[str, Any]:
        """
        Report properties contain an optional SQL source query. Due to a typing
        bug in the mstrio package, the typing must be ignored.
        """
        properties = self._common_entity_properties(report, project_id)  # type: ignore
        properties["url"] = format_url(entity=report, hostname=self.hostname)  # type: ignore
        properties["sql"] = safe_get_property(report, "sql")  # type: ignore
        return properties

    @staticmethod
    def _user_properties(user: User, project_id: str) -> dict[str, Any]:
        return {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "email": user.default_email_address,
        }

    def _fetch_entities(
        self,
        extract_callback: Callable,
        with_url: bool = True,
        with_description: bool = True,
        custom_property_extractor: Callable | None = None,
    ) -> Iterator[dict[str, Any]]:
        """
        Yields all entities across all projects using the given retrieval
        function from the mstrio package.
        """
        for project_id in self.project_ids:
            self.connection.select_project(project_id=project_id)

            entities = extract_callback(connection=self.connection)

            for entity in entities:
                try:
                    if custom_property_extractor:
                        yield custom_property_extractor(entity, project_id)
                    else:
                        yield self._common_entity_properties(
                            entity,
                            project_id=project_id,
                            with_url=with_url,
                            with_description=with_description,
                        )
                except IServerError as e:
                    logger.error(
                        f"Could not fetch attributes for entity {entity.id}: {e}"
                    )

    def _fetch_attributes(self) -> Iterator[dict[str, Any]]:
        return self._fetch_entities(
            list_attributes,
            custom_property_extractor=self._attributes_properties,
        )

    def _fetch_cubes(self) -> Iterator[dict[str, Any]]:
        return self._fetch_entities(list_olap_cubes)

    def _fetch_dashboards(self) -> Iterator[dict[str, Any]]:
        return self._fetch_entities(list_dashboards)

    def _fetch_documents(self) -> Iterator[dict[str, Any]]:
        return self._fetch_entities(list_documents)

    def _fetch_facts(self) -> Iterator[dict[str, Any]]:
        """Yields all facts. Descriptions are not needed for this entity type."""
        return self._fetch_entities(
            list_facts,
            with_url=False,
            with_description=False,
        )

    def _fetch_logical_tables(self) -> Iterator[dict[str, Any]]:
        """
        Yields all logical tables, including their physical tables and their columns.
        """
        return self._fetch_entities(
            list_logical_tables,
            custom_property_extractor=self._logical_table_properties,
        )

    def _fetch_metrics(self) -> Iterator[dict[str, Any]]:
        return self._fetch_entities(
            list_metrics,
            with_url=False,
        )

    def _fetch_reports(self) -> Iterator[dict[str, Any]]:
        return self._fetch_entities(
            list_reports,
            custom_property_extractor=self._report_properties,
        )

    def _fetch_users(self) -> Iterator[dict[str, Any]]:
        """Fetches users across all projects and removes duplicates."""
        users = self._fetch_entities(
            list_users,
            custom_property_extractor=self._user_properties,
        )

        seen_ids: set[str] = set()
        for user in users:
            id_ = user["id"]
            if id_ not in seen_ids:
                yield user
                seen_ids.add(id_)

    def fetch(self, asset: StrategyAsset):
        """Fetch the given asset type from Strategy"""
        if asset == StrategyAsset.ATTRIBUTE:
            yield from self._fetch_attributes()

        elif asset == StrategyAsset.CUBE:
            yield from self._fetch_cubes()

        elif asset == StrategyAsset.DASHBOARD:
            yield from self._fetch_dashboards()

        elif asset == StrategyAsset.DOCUMENT:
            yield from self._fetch_documents()

        elif asset == StrategyAsset.FACT:
            yield from self._fetch_facts()

        elif asset == StrategyAsset.LOGICAL_TABLE:
            yield from self._fetch_logical_tables()

        elif asset == StrategyAsset.METRIC:
            yield from self._fetch_metrics()

        elif asset == StrategyAsset.REPORT:
            yield from self._fetch_reports()

        elif asset == StrategyAsset.USER:
            yield from self._fetch_users()

        else:
            raise NotImplementedError(f"Asset type {asset} not implemented yet")
