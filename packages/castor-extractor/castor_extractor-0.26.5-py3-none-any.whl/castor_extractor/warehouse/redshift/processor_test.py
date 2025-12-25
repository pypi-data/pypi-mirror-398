from datetime import datetime

from .processor import RedshiftExtractionProcessor
from .types import AssembledQuery


def test__assemble_all() -> None:
    # build stream of query parts (intentionally out of order and mixed)
    parts = iter(
        [
            {
                "query_id": 1,
                "text": "FROM toto",
                "sequence": 3,  # third part of statement
                "sequence_count": 3,  # the third part is also the last part
            },
            {
                "query_id": 1,
                "text": "SELECT ",  # first part of statement
                "sequence": 1,
                "sequence_count": 3,
            },
            {
                "query_id": 2,
                "text": "INSERT INTO t ",
                "sequence": 1,
                "sequence_count": 2,
            },
            {
                "query_id": 1,
                "text": "* ",
                "sequence": 2,
                "sequence_count": 3,
            },  # second part of statement
            {
                "query_id": 2,
                "text": "VALUES (1,2,3);",
                "sequence": 2,
                "sequence_count": 2,
            },
        ]
    )

    processor = object.__new__(RedshiftExtractionProcessor)
    results = processor._assemble_all(parts)

    # Convert to a mapping for easy assertions
    by_query = {query.query_id: query.text for query in results}

    # Query IDs are stringified in the implementation
    expected_1 = "SELECT * FROM toto"  # "SELECT " + "* " + "FROM toto"
    assert by_query["1"] == expected_1

    # INSERT ... VALUES (...) should be normalized to DEFAULT VALUES
    assert by_query["2"].startswith("INSERT INTO t ")
    assert "DEFAULT VALUES" in by_query["2"]
    assert "VALUES (" not in by_query["2"]


def test__reconcile() -> None:
    """Test reconciliation of assembled queries with metadata"""
    # Assembled queries
    queries_text = iter(
        [
            AssembledQuery(query_id="1", text="SELECT * FROM users"),
            AssembledQuery(
                query_id="2", text="INSERT INTO logs DEFAULT VALUES"
            ),
            # for query 3 somehow it won't have corresponding metadata, but in practice this case cannot happen
            AssembledQuery(
                query_id="3", text="UPDATE products SET price = 100"
            ),
        ]
    )

    # metadata dictionaries that will serve as reference
    queries_metadata = iter(
        [
            {
                "query_id": "1",
                "aborted": 0,
                "database_id": 100,
                "database_name": "test_db",
                "end_time": datetime(2024, 1, 1, 12, 0, 0),
                "label": "query_1",
                "process_id": "proc_1",
                "start_time": datetime(2024, 1, 1, 11, 59, 0),
                "user_id": 1,
                "user_name": "test_user",
            },
            {
                "query_id": "2",
                "aborted": 0,
                "database_id": 100,
                "database_name": "test_db",
                "end_time": datetime(2024, 1, 1, 12, 1, 0),
                "label": "query_2",
                "process_id": "proc_2",
                "start_time": datetime(2024, 1, 1, 12, 0, 0),
                "user_id": 2,
                "user_name": "admin",
            },
            # Metadata for query_id "4" that has no matching query text
            {
                "query_id": "4",
                "aborted": 1,
                "database_id": 200,
                "database_name": "other_db",
                "end_time": datetime(2024, 1, 1, 12, 2, 0),
                "label": "query_4",
                "process_id": "proc_4",
                "start_time": datetime(2024, 1, 1, 12, 1, 0),
                "user_id": 3,
                "user_name": "other_user",
            },
        ]
    )

    results = list(
        RedshiftExtractionProcessor._reconcile(queries_text, queries_metadata)
    )

    # Should only return queries that have matching metadata
    assert len(results) == 2

    # query_id "1"
    result_1 = next(r for r in results if r["query_id"] == "1")
    assert result_1["query_text"] == "SELECT * FROM users"
    assert result_1["database_name"] == "test_db"
    assert result_1["user_name"] == "test_user"
    assert result_1["aborted"] == 0

    # query_id "2"
    result_2 = next(r for r in results if r["query_id"] == "2")
    assert result_2["query_text"] == "INSERT INTO logs DEFAULT VALUES"
    assert result_2["database_name"] == "test_db"
    assert result_2["user_name"] == "admin"
    assert result_2["aborted"] == 0

    # Query "3" should not appear (no matching metadata, should not happen in real life)
    assert not any(r["query_id"] == "3" for r in results)

    # Query "4" should not appear (no matching query text)
    assert not any(r["query_id"] == "4" for r in results)
