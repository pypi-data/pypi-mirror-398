from .utils import pages_to_database_ids, pages_to_folder_ids


def test_pages_to_folder_ids():
    """Test the pages_to_folder_ids function."""
    pages = [
        {"id": "9", "parentId": None, "parentType": None},
        {"id": "8", "parentId": "2", "parentType": "folder"},
        {"id": "7", "parentId": "9", "parentType": "page"},
        {"id": "6", "parentId": "4", "parentType": "folder"},
        {"id": "5", "parentId": "4", "parentType": "folder"},
    ]
    expected = {"2", "4"}
    result = pages_to_folder_ids(pages)
    assert result == expected


def test_pages_to_database_id():
    """Test the pages_to_database_id function."""
    pages = [
        {"id": "1", "parentId": "db1", "parentType": "database"},
        {"id": "2", "parentId": "db2", "parentType": "database"},
        {"id": "3", "parentId": "4", "parentType": "folder"},
        {"id": "4", "parentId": None, "parentType": None},
        {"id": "5", "parentId": "db1", "parentType": "database"},
        {"id": "6", "parentId": "9", "parentType": "page"},
    ]
    expected = {"db1", "db2"}
    result = pages_to_database_ids(pages)
    assert result == expected
