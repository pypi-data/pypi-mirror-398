from unittest import mock
from unittest.mock import MagicMock

import pytest

from .client import StrategyClient
from .credentials import StrategyCredentials
from .properties import (
    ObjectSubTypes,
    ObjectTypes,
    format_url,
)

_LOCATION = "Project/ABC123/Folder/My Document"
_NAME = "My Document"
_PROJECT_ID = "ABC123"

_CUBE_ID = "CUBE"
_DASHBOARD_ID = "DASH"
_DOCUMENT_ID = "DOC"
_FOLDER_ID = "FOLD"
_REPORT_ID = "REP"


@pytest.fixture
def mocked_cube():
    cube = MagicMock()
    cube.ancestors = [{"id": _FOLDER_ID, "level": 1}]
    cube.id = _CUBE_ID
    cube.project_id = _PROJECT_ID
    cube.subtype = ObjectSubTypes.OLAP_CUBE.value
    cube.type = ObjectTypes.REPORT_DEFINITION
    return cube


@pytest.fixture
def mocked_dashboard():
    dashboard = MagicMock()
    dashboard.id = _DASHBOARD_ID
    dashboard.project_id = _PROJECT_ID
    dashboard.type = ObjectTypes.DOCUMENT_DEFINITION
    return dashboard


@pytest.fixture
def mocked_document():
    document = MagicMock()
    document.id = _DOCUMENT_ID
    document.location = _LOCATION
    document.name = _NAME
    document.project_id = _PROJECT_ID
    document.type = ObjectTypes.DOCUMENT_DEFINITION
    return document


@pytest.fixture
def mocked_report():
    report = MagicMock()
    report.id = _REPORT_ID
    report.project_id = _PROJECT_ID
    report.type = ObjectTypes.REPORT_DEFINITION
    return report


def test_format_url(
    mocked_cube,
    mocked_dashboard,
    mocked_document,
    mocked_report,
):
    credentials = StrategyCredentials(
        base_url="https://reporting.catysserie.com/MicroStrategyLibrary",
        username="user",
        password="pass",
        project_ids=[_PROJECT_ID],
    )

    connection_path = "source.packages.extractor.castor_extractor.visualization.strategy.client.client.Connection"
    is_dashboard_path = "source.packages.extractor.castor_extractor.visualization.strategy.client.properties.is_dashboard"
    with (
        mock.patch(connection_path),
        mock.patch(is_dashboard_path) as mock_is_dashboard,
    ):
        client = StrategyClient(credentials)
        assert client.hostname == "reporting.catysserie.com"

        assert (
            format_url(mocked_cube, client.hostname)
            == "https://reporting.catysserie.com/MicroStrategy/servlet/mstrWeb?folderID=FOLD&projectID=ABC123"
        )

        mock_is_dashboard.return_value = True
        assert (
            format_url(mocked_dashboard, client.hostname)
            == "https://reporting.catysserie.com/MicroStrategyLibrary/app/ABC123/DASH"
        )

        mock_is_dashboard.return_value = False
        assert (
            format_url(mocked_document, client.hostname)
            == "https://reporting.catysserie.com/MicroStrategy/servlet/mstrWeb?documentID=DOC&projectID=ABC123"
        )

        assert (
            format_url(mocked_report, client.hostname)
            == "https://reporting.catysserie.com/MicroStrategy/servlet/mstrWeb?reportID=REP&projectID=ABC123"
        )


def test_StrategyClient__common_entity_properties(mocked_document):
    credentials = StrategyCredentials(
        base_url="https://reporting.catysserie.com/MicroStrategyLibrary",
        username="user",
        password="pass",
        project_ids=[_PROJECT_ID],
    )

    connection_path = "source.packages.extractor.castor_extractor.visualization.strategy.client.client.Connection"
    list_deps_path = "source.packages.extractor.castor_extractor.visualization.strategy.client.client.list_dependencies"
    safe_get_attr_path = "source.packages.extractor.castor_extractor.visualization.strategy.client.client.safe_get_property"
    url_path = "source.packages.extractor.castor_extractor.visualization.strategy.client.client.format_url"

    with (
        mock.patch(connection_path),
        mock.patch(list_deps_path) as mock_list_deps,
        mock.patch(safe_get_attr_path) as mock_safe_get_attr,
        mock.patch(url_path) as mock_url_path,
    ):
        client = StrategyClient(credentials)

        # mock url
        url = "https://some.url.com/document"
        mock_url_path.return_value = url

        # mock dependencies
        mock_list_deps.return_value = [
            {"id": "1", "name": "attr", "subtype": 666, "type": 12}
        ]

        # mock _safe_get_attribute
        description = "some description"
        mock_safe_get_attr.return_value = description

        properties = client._common_entity_properties(
            mocked_document, project_id=_PROJECT_ID
        )

        assert properties["description"] == description
        assert properties["id"] == _DOCUMENT_ID
        assert properties["location"] == _LOCATION
        assert properties["name"] == _NAME
        assert properties["type"] == ObjectTypes.DOCUMENT_DEFINITION.value
        assert properties["url"] == url
        assert properties["project_id"] == _PROJECT_ID

        mock_url_path.reset_mock()
        mock_safe_get_attr.reset_mock()

        properties_no_url_or_desc = client._common_entity_properties(
            mocked_document,
            project_id=_PROJECT_ID,
            with_url=False,
            with_description=False,
        )
        assert "url" not in properties_no_url_or_desc
        assert "description" not in properties_no_url_or_desc
        assert mock_url_path.call_count == 0
        assert mock_safe_get_attr.call_count == 0
