import logging
from enum import Enum
from typing import Any

from mstrio.helpers import IServerError  # type: ignore
from mstrio.modeling import (  # type: ignore
    Attribute,
    TableColumn,
)
from mstrio.types import ObjectSubTypes, ObjectTypes  # type: ignore
from mstrio.utils.entity import Entity  # type: ignore
from mstrio.utils.helper import is_dashboard  # type: ignore
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

_BATCH_SIZE: int = 100


class URLTemplates(Enum):
    DASHBOARD = "https://{hostname}/MicroStrategyLibrary/app/{project_id}/{id_}"
    DOCUMENT = "https://{hostname}/MicroStrategy/servlet/mstrWeb?documentID={id_}&projectID={project_id}"
    REPORT = "https://{hostname}/MicroStrategy/servlet/mstrWeb?reportID={id_}&projectID={project_id}"
    FOLDER = "https://{hostname}/MicroStrategy/servlet/mstrWeb?folderID={id_}&projectID={project_id}"


class Dependency(BaseModel):
    id: str
    name: str
    subtype: int
    type: int

    model_config = ConfigDict(extra="ignore")


def list_dependencies(entity: Entity) -> list[dict]:
    """Lists the entity's dependencies, keeping only relevant fields."""
    dependencies: list[dict] = []

    offset = 0
    while True:
        batch = entity.list_dependencies(offset=offset, limit=_BATCH_SIZE)
        dependencies.extend(batch)
        if len(batch) < _BATCH_SIZE:
            break
        offset += _BATCH_SIZE

    return [
        Dependency(**dependency).model_dump() for dependency in dependencies
    ]


def _is_dashboard(entity: Entity) -> bool:
    """
    Returns True if the entity is a Dashboard. They can only be distinguished
    from Documents by checking the `view_media` property.
    """
    is_type_document = entity.type == ObjectTypes.DOCUMENT_DEFINITION
    return is_type_document and is_dashboard(entity.view_media)


def _is_report(entity: Entity) -> bool:
    """
    Returns True if the entity is a Report. Cubes share the same type as Reports,
    so the subtype must be checked.
    """
    is_type_report = entity.type == ObjectTypes.REPORT_DEFINITION
    is_subtype_cube = entity.subtype == ObjectSubTypes.OLAP_CUBE.value
    return is_type_report and not is_subtype_cube


def format_url(entity: Entity, hostname: str) -> str:
    """
    Formats the right URL.
    * Dashboards : viewed in MicroStrategy
    * Reports and Documents : viewed in MicroStrategy Web
    * other (i.e. Cubes): the URL leads to the folder in MicroStrategy Web
    """
    if _is_dashboard(entity):
        id_ = entity.id
        template = URLTemplates.DASHBOARD

    elif entity.type == ObjectTypes.DOCUMENT_DEFINITION:
        id_ = entity.id
        template = URLTemplates.DOCUMENT

    elif _is_report(entity):
        id_ = entity.id
        template = URLTemplates.REPORT

    else:
        # default to folder URL
        id_ = level_1_folder_id(entity.ancestors)
        template = URLTemplates.FOLDER

    return template.value.format(
        hostname=hostname,
        id_=id_,
        project_id=entity.project_id,
    )


def safe_get_property(entity: Entity, attribute: str) -> str | None:
    """
    Some properties may raise an error. Example: retrieving a Report's `sql` fails if the Report has not been published.
    This safely returns the attribute value, or None if the retrieval fails.
    """
    try:
        value = getattr(entity, attribute)
    except (IServerError, ValueError) as e:
        logger.error(f"Could not get {attribute} for entity {entity.id}: {e}")
        value = None
    return value


def column_properties(columns: list[TableColumn]) -> list[dict[str, Any]]:
    """Returns the properties of a physical table's columns."""
    properties: list[dict[str, Any]] = []

    for column in columns:
        column_properties = {
            "id": column.id,
            "name": column.name,
            "column_name": column.column_name,
        }
        properties.append(column_properties)

    return properties


def level_1_folder_id(folders: list[dict]) -> str:
    """Searches for the first enclosing folder and returns its ID."""
    for folder in folders:
        if folder["level"] == 1:
            return folder["id"]

    raise ValueError("No level 1 folder found")


def lookup_table_id(attribute: Attribute):
    """Returns the lookup table's ID, if there is one."""
    lookup_table = attribute.attribute_lookup_table
    if not lookup_table:
        return None
    return lookup_table.object_id
