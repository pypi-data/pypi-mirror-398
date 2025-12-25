from unittest.mock import Mock

from .sources_transformer import SigmaSourcesTransformer

_ALL_SOURCES = [
    {
        "asset_id": "asset1",
        "sources": [
            {"type": "dataset", "inodeId": "1234"},  # non-table source
            {"type": "table", "inodeId": "table1"},
            {"type": "table", "inodeId": "table2"},
        ],
    },
    {
        "asset_id": "asset2",
        "sources": [
            {"type": "table", "inodeId": "table1"},  # repeated source
        ],
    },
]


_TABLE_TO_PATH = {
    "table1": {
        "connectionId": "conn1",
        "path": ["db", "schema", "table1"],
    },
    "table2": {
        "connectionId": "conn2",
        "path": ["db", "schema", "table2"],
    },
}


def test__map_table_id_to_connection_path():
    transformer = SigmaSourcesTransformer(api_client=Mock())

    def mock_get(endpoint):
        if "table1" in endpoint:
            return _TABLE_TO_PATH["table1"]
        elif "table2" in endpoint:
            return _TABLE_TO_PATH["table2"]
        else:
            raise ValueError(f"Unexpected endpoint: {endpoint}")

    transformer.api_client._get.side_effect = mock_get

    result = transformer._map_table_id_to_connection_path(_ALL_SOURCES)

    assert len(result) == 2
    assert result["table1"] == {
        "connectionId": "conn1",
        "path": ["db", "schema", "table1"],
    }
    assert result["table2"] == {
        "connectionId": "conn2",
        "path": ["db", "schema", "table2"],
    }
    assert transformer.api_client._get.call_count == 2


def test__transform_sources():
    transformer = SigmaSourcesTransformer(api_client=Mock())

    result = list(transformer._transform_sources(_ALL_SOURCES, _TABLE_TO_PATH))

    assert len(result) == 2

    asset_1_results = result[0]
    assert len(asset_1_results["sources"]) == 3
    actual_sources = sorted(
        asset_1_results["sources"], key=lambda x: x["inodeId"]
    )
    expected_sources = [
        {"type": "dataset", "inodeId": "1234"},
        {
            "type": "table",
            "inodeId": "table1",
            "connectionId": "conn1",
            "path": ["db", "schema", "table1"],
        },
        {
            "type": "table",
            "inodeId": "table2",
            "connectionId": "conn2",
            "path": ["db", "schema", "table2"],
        },
    ]
    expected_sources = sorted(expected_sources, key=lambda x: x["inodeId"])
    assert actual_sources == expected_sources

    asset_2_results = result[1]
    assert asset_2_results["asset_id"] == "asset2"
    assert asset_2_results["sources"] == [
        {
            "type": "table",
            "inodeId": "table1",
            "connectionId": "conn1",
            "path": ["db", "schema", "table1"],
        }
    ]
