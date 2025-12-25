from .client import SigmaClient


def test_SigmaClient__yield_deduplicated_queries():
    workbook_id = "workbook1"
    mock_queries = [
        {"elementId": "element1", "name": "Query 1"},
        {"elementId": "element2", "name": "Query 2"},
        {"elementId": "element1", "name": "Query 1"},  # Duplicate
        {"elementId": "element3", "name": "Query 3"},
    ]

    queries = list(
        SigmaClient._yield_deduplicated_queries(mock_queries, workbook_id)
    )

    assert len(queries) == 3
    for query in queries:
        assert query["workbook_id"] == workbook_id
